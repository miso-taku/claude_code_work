# 実装ガイド (Implementation Guide)

本プロジェクトの技術スタック（Python 3.12 + uv）に基づくコーディング規約です。

**前提となる必須ルール**:
- 実装手法: TDD必須（`.claude/guides/tdd.md` 準拠。テストを先に書く）
- 設計手法: DDD必須（`.claude/guides/ddd.md` 準拠。ビジネスルールはドメイン層に置く）
- プロジェクト固有規約: `docs/development-guidelines.md`（存在する場合は最優先）

## Python 規約

### 型ヒント

**すべての関数・メソッドに型ヒントを付ける**:
```python
# ✅ 良い例: 引数・戻り値に型ヒント
def calculate_total(prices: list[int]) -> int:
    return sum(prices)

# ❌ 悪い例: 型ヒントなし
def calculate_total(prices):
    return sum(prices)
```

**組み込みジェネリクスを使用する（Python 3.9+の記法）**:
```python
# ✅ 良い例: 組み込み型をそのまま使用
def count_items(items: list[str]) -> dict[str, int]: ...
def find_task(task_id: UUID) -> Task | None: ...

# ❌ 悪い例: typingモジュールの旧記法
from typing import List, Dict, Optional
def count_items(items: List[str]) -> Dict[str, int]: ...
def find_task(task_id: UUID) -> Optional[Task]: ...
```

**構造の表現**:
```python
# データ構造: dataclassを使用（DDDの値オブジェクトはfrozen=True）
from dataclasses import dataclass

@dataclass(frozen=True)
class Money:
    amount: int
    currency: str = "JPY"

# 選択肢の集合: Enumを使用（文字列リテラルの散在を避ける）
from enum import Enum

class TaskStatus(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

# 抽象インターフェース: ABCを使用（DDDのリポジトリインターフェース等）
from abc import ABC, abstractmethod

class TaskRepository(ABC):
    @abstractmethod
    def find_by_id(self, task_id: UUID) -> Task | None: ...

# 型エイリアス: type文（Python 3.12+）
type TaskId = UUID
```

### 命名規則

**変数・関数**:
```python
# 変数: snake_case、名詞
user_name = "John"
task_list: list[Task] = []

# 関数: snake_case、動詞で始める
def fetch_user_data() -> UserData: ...
def validate_email(email: str) -> None: ...
def calculate_total_price(items: list[Item]) -> Money: ...

# Boolean: is_, has_, should_, can_ で始める
is_valid = True
has_permission = False
should_retry = True
can_delete = False
```

**クラス・例外**:
```python
# クラス: PascalCase、名詞（ユビキタス言語を使う）
class Order: ...
class ConfirmOrderUseCase: ...

# 抽象基底クラス: PascalCase（Iプレフィックスは付けない）
class OrderRepository(ABC): ...   # ✅
class IOrderRepository(ABC): ...  # ❌

# 例外: PascalCase + Errorサフィックス
class ValidationError(Exception): ...
class OrderNotFoundError(Exception): ...
```

**定数**:
```python
# UPPER_SNAKE_CASE（モジュールレベルに定義）
MAX_RETRY_COUNT = 3
API_BASE_URL = "https://api.example.com"
DEFAULT_TIMEOUT_SECONDS = 5.0
```

**モジュール・パッケージ名**:
```python
# モジュール: snake_case
# order_repository.py, confirm_order.py

# テストモジュール: test_ プレフィックスで実装と対応させる
# order.py ↔ test_order.py
```

**プライベート**:
```python
# 外部に公開しない属性・メソッドは _ プレフィックス
class ConfirmOrderUseCase:
    def __init__(self, order_repository: OrderRepository) -> None:
        self._order_repository = order_repository
```

### 関数設計

**単一責務の原則**:
```python
# ✅ 良い例: 単一の責務
def calculate_total_price(items: list[CartItem]) -> Money:
    return sum((item.subtotal() for item in items), Money(0))

def format_price(amount: Money) -> str:
    return f"¥{amount.amount:,}"

# ❌ 悪い例: 計算と整形という複数の責務
def calculate_and_format_price(items: list[CartItem]) -> str: ...
```

**関数の長さ**:
- 目標: 20行以内
- 推奨: 50行以内
- 100行以上: リファクタリングを検討

**引数の数（4個以上はまとめる）**:
```python
# ✅ 良い例: dataclassでまとめる + キーワード専用引数
@dataclass(frozen=True)
class CreateTaskCommand:
    title: str
    description: str = ""
    priority: Priority = Priority.MEDIUM
    due_date: date | None = None

def create_task(command: CreateTaskCommand) -> Task: ...

# ❌ 悪い例: 引数が多すぎる
def create_task(title, description, priority, due_date, tags, assignee): ...
```

**ミュータブルなデフォルト引数の禁止**:
```python
# ✅ 良い例
def add_tags(task: Task, tags: list[str] | None = None) -> None:
    tags = tags if tags is not None else []

# ❌ 悪い例: デフォルト値が呼び出し間で共有されるバグの温床
def add_tags(task: Task, tags: list[str] = []) -> None: ...
```

### エラーハンドリング

**カスタム例外の定義（DDDのレイヤーに対応させる）**:
```python
# domain/exceptions.py — ビジネスルール違反
class DomainError(Exception):
    """ビジネスルール違反を表す基底例外"""

class OrderNotFoundError(DomainError):
    def __init__(self, order_id: UUID) -> None:
        super().__init__(f"注文が見つかりません: {order_id}")
        self.order_id = order_id

# infrastructure層 — 技術的エラー
class StorageError(Exception):
    """永続化処理の失敗を表す例外"""
```

**エラーハンドリングパターン**:
```python
# ✅ 良い例: 予期されるエラーは具体的に捕捉し、技術的エラーはfrom付きでラップ
def get_task(self, task_id: UUID) -> Task:
    try:
        task = self._repository.find_by_id(task_id)
    except OSError as e:
        raise StorageError("タスクの取得に失敗しました") from e

    if task is None:
        raise TaskNotFoundError(task_id)
    return task

# ❌ 悪い例1: 裸のexcept・エラーの握りつぶし
def get_task(self, task_id: UUID) -> Task | None:
    try:
        return self._repository.find_by_id(task_id)
    except Exception:
        return None  # エラー情報が失われる

# ❌ 悪い例2: from なしの再送出（原因のトレースバックが失われる）
except OSError:
    raise StorageError("タスクの取得に失敗しました")
```

**エラーメッセージ**:
```python
# ✅ 良い例: 具体的で解決策を示す
raise ValidationError(f"タイトルは1-200文字で入力してください。現在の文字数: {len(title)}")

# ❌ 悪い例: 曖昧で役に立たない
raise ValueError("Invalid input")
```

### コンテキストマネージャとリソース管理

```python
# ✅ 良い例: with文でリソースを確実に解放
from pathlib import Path

def load_tasks(path: Path) -> list[Task]:
    with path.open(encoding="utf-8") as f:
        return parse_tasks(json.load(f))

# ❌ 悪い例: closeを手動管理（例外時にリークする）
def load_tasks(path: Path) -> list[Task]:
    f = open(path)
    data = json.load(f)
    f.close()
    return parse_tasks(data)
```

**パス操作は `pathlib.Path` を使う**（`os.path` の文字列操作は使わない）。

## コメント規約

### docstring（Google スタイル）

公開する関数・クラス・モジュールにはdocstringを書く:

```python
def create_task(command: CreateTaskCommand) -> Task:
    """タスクを作成する。

    Args:
        command: 作成するタスクの内容。

    Returns:
        作成されたタスク。

    Raises:
        ValidationError: タイトルが不正な場合。
        StorageError: 永続化に失敗した場合。
    """
```

### インラインコメント

**良いコメント**:
```python
# ✅ 理由を説明
# キャッシュを無効化して最新データを取得
cache.clear()

# ✅ 複雑なロジックを説明
# Kadaneのアルゴリズムで最大部分配列和を計算。時間計算量: O(n)

# ✅ TODO・FIXMEを活用（Issue番号付き）
# TODO: キャッシュ機能を実装 (Issue #123)
# FIXME: 大量データでパフォーマンス劣化 (Issue #456)
```

**悪いコメント**:
```python
# ❌ コードの内容を繰り返すだけ
i += 1  # iを1増やす

# ❌ コメントアウトされたコード（削除すべき。履歴はgitにある）
# old_implementation()
```

## セキュリティ

### 入力検証

```python
# ✅ 良い例: 値オブジェクトの生成時にバリデーション（DDD）
import re
from dataclasses import dataclass

@dataclass(frozen=True)
class EmailAddress:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("メールアドレスは必須です")
        if len(self.value) > 254:
            raise ValueError("メールアドレスが長すぎます")
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", self.value):
            raise ValueError("メールアドレスの形式が不正です")

# ❌ 悪い例: 検証されていないstrがシステム内を流れる
def register_user(email: str) -> None: ...
```

### 機密情報の管理

```python
# ✅ 良い例: 環境変数から読み込み
import os

api_key = os.environ.get("API_KEY")
if not api_key:
    raise RuntimeError("API_KEY環境変数が設定されていません")

# ❌ 悪い例: ハードコード（絶対にしない）
api_key = "sk-1234567890abcdef"
```

### インジェクション対策

```python
# ✅ 良い例: プレースホルダを使用
cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))

# ❌ 悪い例: 文字列結合（SQLインジェクション）
cursor.execute(f"SELECT * FROM tasks WHERE id = '{task_id}'")

# ✅ 外部コマンドはリスト形式で渡す（shell=Trueを避ける）
subprocess.run(["git", "status"], check=True)
```

## パフォーマンス

### データ構造の選択

```python
# ✅ 良い例: 繰り返し検索するならdictでO(1)アクセス
task_map = {task.id: task for task in tasks}
task = task_map.get(task_id)

# ❌ 悪い例: 繰り返しの線形探索 O(n)
task = next((t for t in tasks if t.id == task_id), None)

# ✅ 所属チェックはsetで
completed_ids = {t.id for t in completed_tasks}
if task.id in completed_ids: ...
```

### イテレーションの最適化

```python
# ✅ 良い例: 内包表記・ジェネレータ・直接イテレーション
names = [task.name for task in tasks]
total = sum(item.price for item in items)  # ジェネレータで中間リスト不要
for index, item in enumerate(items): ...

# ❌ 悪い例: インデックス経由の冗長なループ
names = []
for i in range(len(tasks)):
    names.append(tasks[i].name)
```

### メモ化

```python
# 純粋関数の重い計算は functools.cache でキャッシュ
from functools import cache

@cache
def expensive_calculation(key: str) -> Result: ...
```

## テストコード

**テストの書き方・実行手順の正式なルールは `.claude/guides/tdd.md` に従うこと**（テストファースト、Red-Green-Refactor、AAA構造、日本語テスト名）。以下は規約の要点のみ。

```python
# tests/unit/domain/models/test_order.py
import pytest

class TestOrderConfirm:
    def test_明細のある注文は確定できる(self) -> None:
        # Arrange（準備）
        order = Order(lines=[OrderLine(product_id=uuid4(), quantity=1)])

        # Act（実行）
        order.confirm()

        # Assert（検証）
        assert order.status is OrderStatus.CONFIRMED

    def test_明細のない注文は確定できない(self) -> None:
        order = Order()

        with pytest.raises(DomainError, match="明細のない注文は確定できない"):
            order.confirm()
```

**テストダブル**: リポジトリ等の抽象（domain層のABC）に対するインメモリ実装（フェイク）を優先する。`unittest.mock.MagicMock` の多用は避け、使う場合も`spec=`で型を固定する。

## リファクタリング

### マジックナンバーの排除

```python
# ✅ 良い例: 定数を定義
MAX_RETRY_COUNT = 3
RETRY_DELAY_SECONDS = 1.0

for attempt in range(MAX_RETRY_COUNT):
    ...

# ❌ 悪い例: マジックナンバー
for attempt in range(3):
    ...
```

### 関数の抽出

```python
# ✅ 良い例: 意図が読める単位に抽出
def process_order(order: Order) -> None:
    _validate_order(order)
    _apply_discounts(order)
    _save_order(order)

# ❌ 悪い例: 検証・計算・永続化が1関数に混在した長い関数
```

### 早期リターンでネストを浅くする

```python
# ✅ 良い例: ガード節
def confirm(self) -> None:
    if not self.lines:
        raise DomainError("明細のない注文は確定できない")
    if self.status is not OrderStatus.DRAFT:
        raise DomainError("下書き状態の注文のみ確定できる")
    self.status = OrderStatus.CONFIRMED

# ❌ 悪い例: if のネストが深い（4レベル以上は禁止）
```

## チェックリスト

実装完了前に確認:

### コード品質
- [ ] 命名が明確で一貫している（snake_case / PascalCase / UPPER_SNAKE_CASE）
- [ ] 全関数に型ヒントがある（組み込みジェネリクス、`X | None`記法）
- [ ] 関数が単一の責務を持っている
- [ ] マジックナンバーがない
- [ ] エラーハンドリングが実装されている（裸のexcept・握りつぶしがない、`raise ... from e`）

### 設計（DDD）
- [ ] ビジネスルールがドメイン層に置かれている
- [ ] レイヤーの依存方向ルールを守っている（`.claude/guides/ddd.md`）

### セキュリティ
- [ ] 入力検証が実装されている（値オブジェクトでの検証を優先）
- [ ] 機密情報がハードコードされていない
- [ ] SQL・コマンドインジェクション対策がされている

### パフォーマンス
- [ ] 適切なデータ構造を使用している（dict/setの活用）
- [ ] 不要な計算・中間リストを避けている

### テスト（TDD）
- [ ] テストコードを実装より先に書いた（`.claude/guides/tdd.md`）
- [ ] `uv run pytest` がパスする
- [ ] 正常系・異常系・境界値がカバーされている

### ドキュメント
- [ ] 公開関数・クラスにdocstring（Googleスタイル）がある
- [ ] 複雑なロジックに理由を説明するコメントがある

### ツール
- [ ] `uv run ruff check .` でエラーがない
- [ ] `uv run ruff format --check .` でフォーマットが統一されている
- [ ] `uv run mypy src` がパスする（導入している場合）
