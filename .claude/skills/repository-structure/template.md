# リポジトリ構造定義書 (Repository Structure Document)

## プロジェクト構造

```
project-root/
├── pyproject.toml         # プロジェクト定義・ツール設定
├── uv.lock                # 依存関係ロックファイル
├── src/                   # ソースコード(srcレイアウト)
│   └── {パッケージ名}/
│       ├── domain/        # [説明]
│       ├── application/   # [説明]
│       ├── infrastructure/# [説明]
│       └── presentation/  # [説明]
├── tests/                 # テストコード
│   ├── unit/              # ユニットテスト
│   └── integration/       # 統合テスト
├── docs/                  # プロジェクトドキュメント
├── config/                # 設定ファイル(該当する場合)
└── scripts/               # 開発補助スクリプト(該当する場合)
```

## ディレクトリ詳細

### src/{パッケージ名}/ (ソースコードディレクトリ)

#### [ディレクトリ1]

**役割**: [説明]

**配置ファイル**:
- [ファイルパターン1]: [説明]
- [ファイルパターン2]: [説明]

**命名規則**:
- [規則1]
- [規則2]

**依存関係**:
- 依存可能: [ディレクトリ名]
- 依存禁止: [ディレクトリ名]

**例**:
```
[ディレクトリ名]/
├── [example_file1].py
└── [example_file2].py
```

#### [ディレクトリ2]

**役割**: [説明]

**配置ファイル**:
- [ファイルパターン1]: [説明]

**命名規則**:
- [規則1]

**依存関係**:
- 依存可能: [ディレクトリ名]
- 依存禁止: [ディレクトリ名]

### tests/ (テストディレクトリ)

#### unit/

**役割**: ユニットテストの配置

**構造**:
```
tests/unit/
└── [layer]/                # src/{パッケージ名}/ と同じ構造
    └── [subdir]/
        └── test_[filename].py
```

**命名規則**:
- パターン: `test_[テスト対象ファイル名].py`
- 例: `src/{パッケージ名}/domain/models/task.py` → `tests/unit/domain/models/test_task.py`

#### integration/

**役割**: 統合テストの配置(複数レイヤー結合のテスト)

**構造**:
```
tests/integration/
└── test_[シナリオ].py       # シナリオ単位でファイル分割
```

### docs/ (ドキュメントディレクトリ)

**配置ドキュメント**:
- `product-requirements.md`: プロダクト要求定義書
- `functional-design.md`: 機能設計書
- `architecture.md`: アーキテクチャ設計書
- `repository-structure.md`: リポジトリ構造定義書(本ドキュメント)
- `development-guidelines.md`: 開発ガイドライン
- `glossary.md`: 用語集

### config/ (設定ファイルディレクトリ - 該当する場合)

**配置ファイル**:
- アプリケーション固有の設定ファイル
- 環境別設定ファイル

**例**:
```
config/
├── default.toml
└── logging.toml
```

※ プロジェクト定義・ツール設定はプロジェクトルートの `pyproject.toml` に集約する

### scripts/ (スクリプトディレクトリ - 該当する場合)

**配置ファイル**:
- 開発環境セットアップスクリプト
- 開発補助スクリプト

## ファイル配置規則

### ソースファイル

| ファイル種別 | 配置先 | 命名規則 | 例 |
|------------|--------|---------|-----|
| [種別1] | [ディレクトリ] | [規則] | [例] |
| [種別2] | [ディレクトリ] | [規則] | [例] |

### テストファイル

| テスト種別 | 配置先 | 命名規則 | 例 |
|-----------|--------|---------|-----|
| ユニットテスト | tests/unit/ (実装と対応するパス構造) | test_[対象].py | test_task_service.py |
| 統合テスト | tests/integration/ | test_[シナリオ].py | test_task_crud.py |

### 設定ファイル

| ファイル種別 | 配置先 | 命名規則 |
|------------|--------|---------|
| プロジェクト定義 | プロジェクトルート | pyproject.toml([project]セクション) |
| ツール設定 | プロジェクトルート | pyproject.toml([tool.ruff], [tool.pytest.ini_options], [tool.mypy]) |
| 依存関係ロック | プロジェクトルート | uv.lock(uvが自動生成・手動編集禁止) |
| 環境設定 | config/ | [環境名].toml |

## 命名規則

### ディレクトリ名

- **レイヤーディレクトリ**: DDDの4層構造に従う
  - 例: `domain/`, `application/`, `infrastructure/`, `presentation/`
- **レイヤー内の格納ディレクトリ**: 複数形、snake_case
  - 例: `models/`, `services/`, `repositories/`, `usecases/`
- **機能ディレクトリ**: snake_case(import可能な名前にする)
  - 例: `task_management/`, `user_authentication/`

### ファイル名

- **モジュールファイル**: snake_case(クラス名はPascalCase)
  - 例: `task_service.py`(class TaskService), `user_repository.py`(class UserRepository)
- **関数モジュール**: snake_case、動詞で始める
  - 例: `format_date.py`, `validate_email.py`
- **定数**: モジュールは snake_case、定数名は UPPER_SNAKE_CASE
  - 例: `constants.py` 内に `API_ENDPOINTS`, `ERROR_MESSAGES`

### テストファイル名

- パターン: `test_[テスト対象].py`
- 例: `test_task_service.py`, `test_format_date.py`

## 依存関係のルール

### レイヤー間の依存

```
presentation(プレゼンテーション層)
    ↓ (OK)
application(アプリケーション層)
    ↓ (OK)
domain(ドメイン層)★中心
    ↑ (OK)
infrastructure(インフラ層)
```

**禁止される依存**:
- domain → application / infrastructure / presentation (❌ ドメイン層は標準ライブラリのみ)
- application → infrastructure / presentation (❌)
- infrastructure → application / presentation (❌)

### モジュール間の依存

**循環依存の禁止**:
```python
# ❌ 悪い例: 循環依存
# module_a.py
from {パッケージ名}.module_b import func_b

# module_b.py
from {パッケージ名}.module_a import func_a  # 循環依存
```

**解決策**:
```python
# ✅ 良い例: 共通モジュールの抽出
# shared.py
class SharedType: ...

# module_a.py
from {パッケージ名}.shared import SharedType

# module_b.py
from {パッケージ名}.shared import SharedType
```

## スケーリング戦略

### 機能の追加

新しい機能を追加する際の配置方針:

1. **小規模機能**: 既存ディレクトリに配置
2. **中規模機能**: レイヤー内にサブディレクトリ(サブパッケージ)を作成
3. **大規模機能**: 独立したモジュールとして分離

**例**:
```
src/{パッケージ名}/
├── domain/
│   └── models/
│       ├── user.py               # 既存機能
│       └── task/                 # 中規模機能の分離(集約単位)
│           ├── task.py
│           ├── subtask.py
│           └── task_category.py
```

### ファイルサイズの管理

**ファイル分割の目安**:
- 1ファイル: 300行以下を推奨
- 300-500行: リファクタリングを検討
- 500行以上: 分割を強く推奨

**分割方法**:
```python
# 悪い例: 1ファイルに全機能
# task_service.py (800行)

# 良い例: 責務ごとに分割
# task_service.py (200行) - CRUD操作
# task_validation_service.py (150行) - バリデーション
# task_notification_service.py (100行) - 通知処理
```

## 特殊ディレクトリ

### .steering/ (ステアリングファイル)

**役割**: 特定の開発作業における「今回何をするか」を定義

**構造**:
```
.steering/
└── [YYYYMMDD]-[task-name]/
    ├── requirements.md      # 今回の作業の要求内容
    ├── design.md            # 変更内容の設計
    └── tasklist.md          # タスクリスト
```

**命名規則**: `20250115-add-user-profile` 形式

### .claude/ (Claude Code設定)

**役割**: Claude Code設定とカスタマイズ

**構造**:
```
.claude/
├── commands/                # スラッシュコマンド
├── skills/                  # タスクモード別スキル
└── agents/                  # サブエージェント定義
```

## 除外設定

### .gitignore

プロジェクトで除外すべきファイル:
- `.venv/`
- `__pycache__/`
- `.pytest_cache/`
- `.ruff_cache/`
- `.mypy_cache/`
- `dist/`
- `.env`
- `.steering/` (タスク管理用の一時ファイル)
- `*.log`
- `.DS_Store`

### ツールの除外設定(pyproject.toml)

ruff・mypy・pytestで除外すべきファイルは `pyproject.toml` の各セクションで指定する:
- `[tool.ruff]` の `exclude`: `.venv/`, `.steering/`
- `[tool.mypy]` の `exclude`: `.venv/`, `.steering/`
- カバレッジ計測対象は `src/` のみとする(`uv run pytest --cov=src`)
