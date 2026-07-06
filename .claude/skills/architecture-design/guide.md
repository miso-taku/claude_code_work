# アーキテクチャ設計ガイド

## 基本原則

### 1. 技術選定には理由を明記

**悪い例**:
```
- Python
- uv
```

**良い例**:
```
- Python 3.12.8
  - 安定版として広くサポートされており、本番環境での安定稼働が期待できる
  - 型ヒント（組み込みジェネリクス、`X | None` 構文）の充実により、静的解析でバグを早期検出でき、保守性が向上
  - PyPIエコシステムが充実しており、必要なライブラリの入手が容易

- uv
  - Rust製で依存関係の解決・インストールが高速であり、開発効率が高い
  - uv.lockによる依存関係の厳密なロックで、環境の再現性が担保される
  - Pythonバージョン管理・仮想環境・パッケージ管理を単一ツールで完結できる

- mypy / Ruff
  - mypyによる静的型チェックで実行前にバグを検出でき、保守性が向上
  - Ruffによるリント・フォーマットの統一で、チーム開発におけるコードの可読性と品質が担保される
```

### 2. レイヤー分離の原則

DDDの4層構造（詳細は `.claude/guides/ddd.md` を参照）に従い、依存関係を一方向に保ちます:

```
presentation → application → domain ← infrastructure (OK)
presentation → domain                                (NG: application層を飛ばさない)
domain → infrastructure                              (NG: ドメイン層は他層に依存しない)
```

### 3. 測定可能な要件

すべてのパフォーマンス要件は測定可能な形で記述します。

## レイヤードアーキテクチャの設計

### 各レイヤーの責務

**プレゼンテーション層（presentation）**:
```python
# 責務: ユーザー入力の受付と形式バリデーション
class Cli:
    def __init__(self, create_task_usecase: CreateTaskUseCase) -> None:
        self._create_task_usecase = create_task_usecase

    # OK: アプリケーション層（ユースケース）を呼び出す
    def add_task(self, title: str) -> None:
        task = self._create_task_usecase.execute(title)
        print(f"Created: {task.id}")

    # NG: インフラ層（リポジトリ実装）を直接呼び出す
    def add_task_bad(self, title: str) -> None:
        self._repository.save(Task(title=title))  # ❌
```

**アプリケーション層（application）**:
```python
# 責務: ユースケースの手順調整（ビジネスルールは書かない）
class CreateTaskUseCase:
    def __init__(self, task_repository: TaskRepository) -> None:
        self._task_repository = task_repository

    def execute(self, title: str) -> Task:
        task = Task.create(title=title)  # ← ビジネスルールはドメイン層
        self._task_repository.save(task)
        return task
```

**ドメイン層（domain）**:
```python
# 責務: ビジネスルール・不変条件の実装（他層に依存しない）
from dataclasses import dataclass, field
from uuid import UUID, uuid4

@dataclass
class Task:
    title: str
    id: UUID = field(default_factory=uuid4)
    priority: Priority = Priority.MEDIUM

    @classmethod
    def create(cls, title: str) -> "Task":
        # ビジネスロジック: 優先度の自動推定
        return cls(title=title, priority=Priority.estimate(title))

# リポジトリのインターフェース（抽象）はdomain層に定義する
from abc import ABC, abstractmethod

class TaskRepository(ABC):
    @abstractmethod
    def save(self, task: Task) -> None: ...
```

**インフラ層（infrastructure）**:
```python
# 責務: データの永続化（domain層のインターフェースを実装）
class JsonTaskRepository(TaskRepository):
    def save(self, task: Task) -> None:
        self._storage.write(task)
```

## パフォーマンス要件の設定

### 具体的な数値目標

```
コマンド実行時間: 100ms以内(平均的なPC環境で)
└─ 測定方法: time.perf_counterでCLI起動から結果表示まで計測
└─ 測定環境: CPU Core i5相当、メモリ8GB、SSD

タスク一覧表示: 1000件まで1秒以内
└─ 測定方法: 1000件のダミーデータで計測
└─ 許容範囲: 100件で100ms、1000件で1秒、10000件で10秒
```

## セキュリティ設計

### データ保護の3原則

1. **最小権限の原則**
```bash
# ファイルパーミッション
chmod 600 ~/.devtask/tasks.json  # 所有者のみ読み書き
```

2. **入力検証**
```python
def validate_title(title: str) -> None:
    if not title:
        raise ValidationError("タイトルは必須です")
    if len(title) > 200:
        raise ValidationError("タイトルは200文字以内です")
```

3. **機密情報の管理**
```bash
# 環境変数で管理
export DEVTASK_API_KEY="xxxxx"  # コード内にハードコードしない
```

## スケーラビリティ設計

### データ増加への対応

**想定データ量**: [例: 10,000件のタスク]

**対策**:
- データのページネーション
- 古いデータのアーカイブ
- インデックスの最適化

```python
# アーカイブ機能の例: 古いタスクを別ファイルに移動
from datetime import datetime

class ArchiveTasksUseCase:
    def __init__(
        self,
        task_repository: TaskRepository,
        archive_storage: ArchiveStorage,
    ) -> None:
        self._task_repository = task_repository
        self._archive_storage = archive_storage

    def execute(self, older_than: datetime) -> None:
        old_tasks: list[Task] = self._task_repository.find_completed(older_than)
        self._archive_storage.save(old_tasks)
        self._task_repository.delete_many([task.id for task in old_tasks])
```

## 依存関係管理

### バージョン管理方針

```toml
# pyproject.toml
[project]
dependencies = [
    "typer>=0.12,<1.0",  # マイナーバージョンアップは許可、メジャーは固定
    "rich==13.7.0",      # 破壊的変更のリスクがある場合は完全固定
]

[dependency-groups]
dev = [
    "pytest>=8.0,<9.0",
    "ruff>=0.6,<0.7",    # 0.x系はマイナーで破壊的変更があり得るため範囲を狭める
    "mypy>=1.10,<2.0",
]
```

**方針**:
- 依存関係の追加は `uv add`（開発用は `uv add --dev`）で行い、pyproject.tomlを手書きしない
- 安定版は `>=x,<次のメジャー` でメジャーバージョンを固定（破壊的変更を防ぐ）
- 破壊的変更のリスクがある場合は `==` で完全固定
- 0.x系のパッケージはマイナーバージョンまで固定範囲を狭める
- 実際にインストールされるバージョンは `uv.lock` で厳密に管理し、コミットに含める（`uv sync` で環境を再現）

## チェックリスト

- [ ] すべての技術選定に理由が記載されている
- [ ] レイヤードアーキテクチャ（DDD 4層構造）が明確に定義されている
- [ ] パフォーマンス要件が測定可能である
- [ ] セキュリティ考慮事項が記載されている
- [ ] スケーラビリティが考慮されている
- [ ] バックアップ戦略が定義されている
- [ ] 依存関係管理のポリシーが明確である
- [ ] テスト戦略（pytest、カバレッジ80%以上）が定義されている
