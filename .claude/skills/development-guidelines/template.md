# 開発ガイドライン (Development Guidelines)

## コーディング規約

### 命名規則

#### 変数・関数

**Python**:
```python
# ✅ 良い例
user_profile_data = fetch_user_profile()
def calculate_total_price(items: list[CartItem]) -> Money: ...

# ❌ 悪い例
data = fetch()
def calc(arr): ...
```

**原則**:
- 変数: snake_case、名詞または名詞句
- 関数: snake_case、動詞で始める
- 定数: UPPER_SNAKE_CASE
- Boolean: `is_`, `has_`, `should_`で始める

#### クラス・インターフェース

```python
# クラス: PascalCase、名詞(ユビキタス言語を使う)
class TaskManager: ...
class UserAuthenticationService: ...

# 抽象基底クラス(インターフェース): PascalCase、Iプレフィックスは付けない
from abc import ABC, abstractmethod

class TaskRepository(ABC):
    @abstractmethod
    def find_by_id(self, task_id: UUID) -> Task | None: ...

# 列挙型: PascalCase(文字列リテラルの散在を避ける)
from enum import Enum

class TaskStatus(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
```

### コードフォーマット

**インデント**: [2スペース/4スペース/タブ]

**行の長さ**: 最大[80/100/120]文字

**例**:
```python
# [言語] コードフォーマット例
[コード例]
```

### コメント規約

**関数・クラスのドキュメント** (Googleスタイルのdocstring):
```python
def count_tasks(
    tasks: list[Task],
    task_filter: TaskFilter | None = None,
) -> int:
    """タスクの合計数を計算する。

    Args:
        tasks: 計算対象のタスクリスト。
        task_filter: フィルター条件(オプション)。

    Returns:
        タスクの合計数。

    Raises:
        ValidationError: タスクリストが不正な場合。
    """
    # 実装
```

**インラインコメント**:
```python
# ✅ 良い例: なぜそうするかを説明
# キャッシュを無効化して、最新データを取得
cache.clear()

# ❌ 悪い例: 何をしているか(コードを見れば分かる)
# キャッシュをクリアする
cache.clear()
```

### エラーハンドリング

**原則**:
- 予期されるエラー: 適切なカスタム例外クラスを定義
- 予期しないエラー: 上位に伝播(握りつぶさない)
- 例外をラップして再送出する場合は `raise ... from e` で原因を保持する

**例**:
```python
# カスタム例外の定義
class ValidationError(Exception):
    def __init__(self, message: str, field: str, value: object) -> None:
        super().__init__(message)
        self.field = field
        self.value = value


# エラーハンドリング
try:
    task = task_service.create(data)
except ValidationError as e:
    print(f"検証エラー [{e.field}]: {e}")
    # ユーザーにフィードバック
except OSError as e:
    # 技術的エラーは原因を保持してラップし、上位に伝播
    raise StorageError("タスクの作成に失敗しました") from e
```

## Git運用ルール

### ブランチ戦略

**ブランチ種別**:
- `main`: 本番環境にデプロイ可能な状態
- `develop`: 開発の最新状態
- `feature/[機能名]`: 新機能開発
- `fix/[修正内容]`: バグ修正
- `refactor/[対象]`: リファクタリング

**フロー**:
```
main
  └─ develop
      ├─ feature/task-management
      ├─ feature/user-auth
      └─ fix/task-validation
```

### コミットメッセージ規約

**フォーマット**:
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type**:
- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメント
- `style`: コードフォーマット
- `refactor`: リファクタリング
- `test`: テスト追加・修正
- `chore`: ビルド、補助ツール等

**例**:
```
feat(task): タスクの優先度設定機能を追加

ユーザーがタスクに優先度(高/中/低)を設定できるようにしました。
- Taskモデルにpriorityフィールドを追加
- CLIに--priorityオプションを追加
- 優先度によるソート機能を実装

Closes #123
```

### プルリクエストプロセス

**作成前のチェック**:
- [ ] 全てのテストがパス (`uv run pytest`)
- [ ] Lintエラーがない (`uv run ruff check .`)
- [ ] 型チェックがパス (`uv run mypy src`)
- [ ] 競合が解決されている

**PRテンプレート**:
```markdown
## 概要
[変更内容の簡潔な説明]

## 変更理由
[なぜこの変更が必要か]

## 変更内容
- [変更点1]
- [変更点2]

## テスト
- [ ] ユニットテスト追加
- [ ] 手動テスト実施

## スクリーンショット(該当する場合)
[画像]

## 関連Issue
Closes #[Issue番号]
```

**レビュープロセス**:
1. セルフレビュー
2. 自動テスト実行
3. レビュアーアサイン
4. レビューフィードバック対応
5. 承認後マージ

## テスト戦略

### テストの種類

#### ユニットテスト

**対象**: 個別の関数・クラス

**カバレッジ目標**: [80/90/100]%

**例**:
```python
# tests/unit/application/usecases/test_create_task.py
import pytest


class TestCreateTask:
    def test_正常なデータの場合タスクを作成できる(self) -> None:
        # Arrange(準備)
        repository = InMemoryTaskRepository()
        usecase = CreateTaskUseCase(repository)
        command = CreateTaskCommand(title="テストタスク", description="説明")

        # Act(実行)
        task = usecase.execute(command)

        # Assert(検証)
        assert task.id is not None
        assert task.title == "テストタスク"

    def test_タイトルが空の場合ValidationErrorになる(self) -> None:
        # Arrange(準備)
        repository = InMemoryTaskRepository()
        usecase = CreateTaskUseCase(repository)

        # Act & Assert(実行と検証)
        with pytest.raises(ValidationError):
            usecase.execute(CreateTaskCommand(title=""))
```

#### 統合テスト

**対象**: 複数コンポーネントの連携

**例**:
```python
# tests/integration/test_task_crud.py
from pathlib import Path


class TestTaskCrud:
    def test_タスクの作成_取得_更新_削除ができる(self, tmp_path: Path) -> None:
        # Arrange(準備): 実際のリポジトリ実装を使用
        service = TaskService(JsonTaskRepository(tmp_path / "tasks.json"))

        # 作成
        created = service.create(CreateTaskCommand(title="テスト"))

        # 取得
        found = service.find_by_id(created.id)
        assert found is not None
        assert found.title == "テスト"

        # 更新
        service.update(created.id, title="更新後")
        updated = service.find_by_id(created.id)
        assert updated is not None
        assert updated.title == "更新後"

        # 削除
        service.delete(created.id)
        assert service.find_by_id(created.id) is None
```

#### E2Eテスト

**対象**: ユーザーシナリオ全体

**例**:
```python
# tests/e2e/test_task_flow.py
class TestTaskManagementFlow:
    def test_ユーザーがタスクを追加して完了できる(self) -> None:
        # タスク追加
        result = run_cli(["add", "新しいタスク"])
        assert "タスクを追加しました" in result.output

        # タスク一覧表示
        result = run_cli(["list"])
        assert "新しいタスク" in result.output

        # タスク完了
        result = run_cli(["complete", "1"])
        assert "タスクを完了しました" in result.output
```

### テスト命名規則

**パターン**: `test_{条件}の場合{結果}になる`(日本語で振る舞いを記述する。詳細は `.claude/guides/tdd.md`)

**例**:
```python
# ✅ 良い例
def test_タイトルが空の場合ValidationErrorになる(self) -> None: ...
def test_存在するIDの場合タスクを返す(self) -> None: ...
def test_存在しないIDを削除した場合TaskNotFoundErrorになる(self) -> None: ...

# ❌ 悪い例
def test_1(self) -> None: ...
def test_works(self) -> None: ...
def test_create_2(self) -> None: ...
```

### モック・スタブの使用

**原則**:
- 外部依存(API、DB、ファイルシステム)はテストダブルに置き換える
- ビジネスロジックは実装を使用
- domain層の抽象(ABC)に対する**インメモリフェイク実装を優先**する
- `unittest.mock` を使う場合は必ず `spec=` で型を固定する

**例**:
```python
# ✅ 優先: リポジトリの抽象(ABC)に対するインメモリフェイク
class InMemoryTaskRepository(TaskRepository):
    def __init__(self) -> None:
        self._tasks: dict[UUID, Task] = {}

    def find_by_id(self, task_id: UUID) -> Task | None:
        return self._tasks.get(task_id)

    def save(self, task: Task) -> None:
        self._tasks[task.id] = task

    def delete(self, task_id: UUID) -> None:
        self._tasks.pop(task_id, None)


# サービスは実際の実装を使用
service = TaskService(InMemoryTaskRepository())

# unittest.mock を使う場合は spec= で型を固定する
from unittest.mock import MagicMock

mock_repository = MagicMock(spec=TaskRepository)
```

## コードレビュー基準

### レビューポイント

**機能性**:
- [ ] 要件を満たしているか
- [ ] エッジケースが考慮されているか
- [ ] エラーハンドリングが適切か

**可読性**:
- [ ] 命名が明確か
- [ ] コメントが適切か
- [ ] 複雑なロジックが説明されているか

**保守性**:
- [ ] 重複コードがないか
- [ ] 責務が明確に分離されているか
- [ ] 変更の影響範囲が限定的か

**パフォーマンス**:
- [ ] 不要な計算がないか
- [ ] メモリリークの可能性がないか
- [ ] データベースクエリが最適化されているか

**セキュリティ**:
- [ ] 入力検証が適切か
- [ ] 機密情報がハードコードされていないか
- [ ] 権限チェックが実装されているか

### レビューコメントの書き方

**建設的なフィードバック**:
```markdown
## ✅ 良い例
この実装だと、タスク数が増えた時にパフォーマンスが劣化する可能性があります。
代わりに、インデックスを使った検索を検討してはどうでしょうか？

## ❌ 悪い例
この書き方は良くないです。
```

**優先度の明示**:
- `[必須]`: 修正必須
- `[推奨]`: 修正推奨
- `[提案]`: 検討してほしい
- `[質問]`: 理解のための質問

## 開発環境セットアップ

### 必要なツール

| ツール | バージョン | インストール方法 |
|--------|-----------|-----------------|
| [ツール1] | [バージョン] | [コマンド] |
| [ツール2] | [バージョン] | [コマンド] |

### セットアップ手順

```bash
# 1. リポジトリのクローン
git clone [URL]
cd [project-name]

# 2. 依存関係のインストール(仮想環境も自動構築)
uv sync

# 3. 環境変数の設定
cp .env.example .env
# .envファイルを編集

# 4. 動作確認
uv run pytest
uv run ruff check .
```

### 推奨開発ツール(該当する場合)

- [ツール1]: [説明]
- [ツール2]: [説明]
