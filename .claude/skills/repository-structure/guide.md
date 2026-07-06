# リポジトリ構造定義書作成ガイド

## 基本原則

### 1. 役割の明確化

各ディレクトリは単一の明確な役割を持つべきです。

**悪い例**:
```
src/{パッケージ名}/
├── stuff/           # 曖昧
├── misc/            # 雑多
└── utils/           # 汎用的すぎる
```

**良い例**:
```
src/{パッケージ名}/
├── domain/          # ビジネスルール(エンティティ・値オブジェクト)
├── application/     # ユースケースの調整
├── infrastructure/  # データ永続化・外部連携
└── presentation/    # CLI / API エンドポイント
```

### 2. レイヤー分離の徹底

アーキテクチャのレイヤー構造(DDDの4層構造)をディレクトリ構造に反映させます:

```
src/{パッケージ名}/
├── presentation/        # プレゼンテーション層
│   └── cli.py           # CLI実装
├── application/         # アプリケーション層
│   └── usecases/        # ユースケース
├── domain/              # ドメイン層(中心)
│   ├── models/          # エンティティ・値オブジェクト・集約
│   ├── services/        # ドメインサービス
│   ├── exceptions.py    # ドメイン例外
│   └── repositories/    # リポジトリインターフェース(抽象)
└── infrastructure/      # インフラ層
    └── repositories/    # リポジトリ実装
```

### 3. srcレイアウトの採用(基本)

Python + uv プロジェクトでは `src/{パッケージ名}/` 形式のsrcレイアウトを採用します:

**基本構造**:
```
project-root/
├── pyproject.toml       # プロジェクト定義・ツール設定
├── uv.lock              # 依存関係ロックファイル
├── src/
│   └── {パッケージ名}/   # アプリケーションパッケージ
└── tests/               # テストコード(unit / integration)
```

**レイヤー構造との対応**:
```
プレゼンテーション層 → presentation/
アプリケーション層   → application/usecases/
ドメイン層           → domain/models/, domain/services/, domain/repositories/
インフラ層           → infrastructure/repositories/
```

## ディレクトリ構造の設計

### レイヤー構造の表現

```
# 悪い例: 平坦な構造
src/{パッケージ名}/
├── task_cli.py
├── task_service.py
├── task_repository.py
├── user_cli.py
├── user_service.py
└── user_repository.py

# 良い例: レイヤーを明確に
src/{パッケージ名}/
├── presentation/
│   ├── task_cli.py
│   └── user_cli.py
├── domain/
│   ├── models/
│   │   ├── task.py
│   │   └── user.py
│   └── repositories/
│       ├── task_repository.py
│       └── user_repository.py
└── infrastructure/
    └── repositories/
        ├── json_task_repository.py
        └── json_user_repository.py
```

### テストディレクトリの配置

**推奨構造**:
```
project-root/
├── src/
│   └── {パッケージ名}/
│       └── domain/
│           └── models/
│               └── task.py
└── tests/
    ├── unit/
    │   └── domain/
    │       └── models/
    │           └── test_task.py
    └── integration/
        └── test_{シナリオ}.py
```

**理由**:
- テストコードが本番コードと分離
- パッケージ配布物にテストが含まれない
- 実装と対応するパス構造で、テスト対象がすぐわかる
- テストタイプ(unit / integration)ごとに整理可能

## 命名規則のベストプラクティス

### ディレクトリ名の原則

**1. 複数形を使う (レイヤー内の格納ディレクトリ)**
```
✅ models/
✅ services/
✅ repositories/
✅ usecases/

❌ model/
❌ service/
❌ repository/
```

理由: 複数のファイルを格納するため

**2. snake_caseを使う**
```
✅ task_management/
✅ user_authentication/

❌ TaskManagement/
❌ task-management/
```

理由: Pythonパッケージとしてimport可能にするため(ハイフンは使用不可)

**3. 具体的な名前を使う**
```
✅ validators/       # 入力検証
✅ formatters/       # データ整形
✅ parsers/          # データ解析

❌ utils/            # 汎用的すぎる
❌ helpers/          # 曖昧
❌ common/           # 意味不明
```

### ファイル名の原則

**1. クラスを含むモジュール: snake_case + 役割接尾辞(クラス名はPascalCase)**
```python
# ユースケースクラス
confirm_order.py          # class ConfirmOrderUseCase
create_task.py            # class CreateTaskUseCase

# リポジトリクラス
task_repository.py        # class TaskRepository(ABC)
json_task_repository.py   # class JsonTaskRepository
```

**2. 関数モジュール: snake_case + 動詞で始める**
```python
# ユーティリティ関数
format_date.py
validate_email.py
parse_command_arguments.py
```

**3. ドメインモデル: snake_case(クラス名はPascalCase)**
```python
# エンティティ・値オブジェクト
task.py                   # class Task
money.py                  # class Money
user_profile.py           # class UserProfile
```

**4. 定数モジュール: snake_case(定数名はUPPER_SNAKE_CASE)**
```python
# constants.py 内で定義
API_ENDPOINTS = {...}
ERROR_MESSAGES = {...}
```

## 依存関係の管理

### レイヤー間の依存ルール

依存方向は `presentation → application → domain ← infrastructure` を厳守します。

```python
# ✅ 良い例: 上位レイヤーから下位レイヤーへの依存
# presentation/task_cli.py
from {パッケージ名}.application.usecases.create_task import CreateTaskUseCase

class TaskCLI:
    def __init__(self, create_task_usecase: CreateTaskUseCase) -> None:
        self._create_task_usecase = create_task_usecase

# ❌ 悪い例: ドメイン層から他レイヤーへの依存
# domain/models/task.py
from {パッケージ名}.infrastructure.repositories.json_task_repository import (
    JsonTaskRepository,  # 禁止！ドメイン層は標準ライブラリのみに依存する
)
```

### 循環依存の回避

**問題のあるコード**:
```python
# domain/services/task_service.py
from {パッケージ名}.domain.services.user_service import UserService

class TaskService:
    def __init__(self, user_service: UserService) -> None:
        self._user_service = user_service

# domain/services/user_service.py
from {パッケージ名}.domain.services.task_service import TaskService  # 循環依存！

class UserService:
    def __init__(self, task_service: TaskService) -> None:
        self._task_service = task_service
```

**解決策1: 抽象(インターフェース)を抽出**
```python
# domain/repositories/task_repository.py
from abc import ABC, abstractmethod

class TaskRepository(ABC):
    @abstractmethod
    def find_by_user_id(self, user_id: UUID) -> list[Task]: ...

# domain/services/user_service.py
from {パッケージ名}.domain.repositories.task_repository import TaskRepository

class UserService:
    def __init__(self, task_repository: TaskRepository) -> None:
        self._task_repository = task_repository  # 抽象に依存(依存性逆転)
```

**解決策2: 依存関係を見直す**
```python
# 共通の機能を別サービスに抽出
# domain/services/notification_service.py
class NotificationService:
    def notify_task_assignment(self, task_id: UUID, user_id: UUID) -> None:
        """通知処理"""

# domain/services/task_service.py
from {パッケージ名}.domain.services.notification_service import NotificationService

class TaskService:
    def __init__(self, notification_service: NotificationService) -> None:
        self._notification_service = notification_service

# domain/services/user_service.py
from {パッケージ名}.domain.services.notification_service import NotificationService

class UserService:
    def __init__(self, notification_service: NotificationService) -> None:
        self._notification_service = notification_service
```

## スケーリング戦略

### 推奨構造

**標準パターン**:
```
src/{パッケージ名}/
├── __init__.py
├── domain/
│   ├── models/
│   │   ├── task.py
│   │   └── user.py
│   ├── services/
│   ├── exceptions.py
│   └── repositories/
│       ├── task_repository.py
│       └── user_repository.py
├── application/
│   └── usecases/
│       ├── create_task.py
│       └── register_user.py
├── infrastructure/
│   └── repositories/
│       ├── json_task_repository.py
│       └── json_user_repository.py
└── presentation/
    └── cli.py
```

**理由**:
- レイヤーごとに責務が明確
- 後からのリファクタリングが不要
- チーム開発で統一しやすい

### モジュール分離のタイミング

**分離を検討する兆候**:
1. ディレクトリ内のファイル数が10個以上
2. 関連する機能がまとまっている
3. 独立してテスト可能
4. 他の機能への依存が少ない

**分離の手順**:
```
# Before: 全てmodels/直下に配置
domain/models/
├── task.py
├── subtask.py
├── task_category.py
├── user.py
└── user_credential.py

# After: 集約(機能)ごとにサブパッケージ化
domain/models/
├── task/
│   ├── task.py
│   ├── subtask.py
│   └── task_category.py
└── user/
    ├── user.py
    └── user_credential.py
```

## 特殊なケースの対応

### 共有コードの配置

**shared/ または common/ ディレクトリ**
```
src/{パッケージ名}/
├── shared/
│   ├── utils/           # 汎用ユーティリティ
│   ├── types/           # 共通型定義(TypeAlias, Protocol)
│   └── constants.py     # 共通定数
├── domain/
├── application/
├── infrastructure/
└── presentation/
```

**ルール**:
- 本当に複数のレイヤーで使われるもののみ
- 単一レイヤーでしか使わないものは含めない
- ドメイン層から参照する場合、shared/は標準ライブラリのみに依存させる

### 設定ファイルの管理(該当する場合)

プロジェクト定義とツール設定は `pyproject.toml` に集約します:

```toml
[project]            # パッケージ名・バージョン・依存関係
[tool.ruff]          # リント・フォーマット設定
[tool.pytest.ini_options]  # テスト設定
[tool.mypy]          # 型チェック設定
```

アプリケーション固有の設定が必要な場合:
```
config/
├── default.toml         # デフォルト設定
└── logging.toml         # ログ設定
```

### スクリプトの管理(該当する場合)

```
scripts/
├── setup_dev.sh         # 開発環境セットアップスクリプト
└── generate_data.py     # 開発補助スクリプト(uv run scripts/generate_data.py で実行)
```

## ドキュメント配置

### ドキュメントの種類と配置先

**プロジェクトルート**:
- `README.md`: プロジェクト概要
- `CONTRIBUTING.md`: 貢献ガイド
- `LICENSE`: ライセンス

**docs/ ディレクトリ**:
- `product-requirements.md`: PRD
- `functional-design.md`: 機能設計書
- `architecture.md`: アーキテクチャ設計書
- `repository-structure.md`: 本ドキュメント
- `development-guidelines.md`: 開発ガイドライン
- `glossary.md`: 用語集

**ソースコード内**:
- docstring(Googleスタイル等): 関数・クラスの説明

## チェックリスト

- [ ] 各ディレクトリの役割が明確に定義されている
- [ ] レイヤー構造(domain / application / infrastructure / presentation)がディレクトリに反映されている
- [ ] srcレイアウト(`src/{パッケージ名}/`)を採用している
- [ ] 命名規則(snake_case)が一貫している
- [ ] テストコードの配置方針(tests/unit/, tests/integration/ が実装と対応するパス構造)が決まっている
- [ ] 依存関係のルール(presentation → application → domain ← infrastructure)が明確である
- [ ] 循環依存がない
- [ ] スケーリング戦略が考慮されている
- [ ] 共有コードの配置ルールが定義されている
- [ ] 設定(pyproject.toml)の管理方法が決まっている
- [ ] ドキュメントの配置場所が明確である
