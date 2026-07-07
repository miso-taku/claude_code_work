# claude_code_work

Claude Code 向けの「スペック駆動開発（Spec-Driven Development）」テンプレートリポジトリです。
ドメイン駆動設計（DDD）とテスト駆動開発（TDD）を前提に、要求定義からドキュメント作成・実装・検証までの一連の開発プロセスを、Claude Code のスキル／コマンド／サブエージェントとして自動化しています。

## 技術スタック

- Python v3.12.8
- パッケージマネージャー: [uv](https://docs.astral.sh/uv/)

## プロジェクト状況ダッシュボード

リポジトリの現在の状況（ロードマップの現在地・永続ドキュメントの整備状況・ステアリング作業の進捗・コミット履歴）を、レトロポップなデザインの単一HTMLとして生成できます。クローン直後の環境でも Python 3.12 + uv + git があれば動作します（実行時の外部依存なし）。

```bash
uv sync          # 初回のみ（依存関係と dashboard コマンドをセットアップ）
uv run dashboard # リポジトリルートに dashboard.html を生成
```

生成された `dashboard.html` をブラウザで開いてください。オプション:

- `--output <パス>`: 出力先HTMLパスを変更（既定: `<root>/dashboard.html`）
- `--root <パス>`: 対象リポジトリのルートを変更（既定: カレントディレクトリ）

実装は `tools/dashboard/`（DDD 4層構造・TDD開発の独立パッケージ）にあります。`src/` と `tests/` はアプリケーション本体専用で、開発支援ツールは含みません。

## 開発の基本原則

このプロジェクトでは以下の2原則を例外なく適用します。詳細は [CLAUDE.md](CLAUDE.md) を参照してください。

1. **設計はドメイン駆動設計（DDD）に従う**（[.claude/guides/ddd.md](.claude/guides/ddd.md)）
   - 設計ドキュメントには必ずドメインモデル（エンティティ・値オブジェクト・集約・リポジトリ）を記載
   - レイヤーは domain / application / infrastructure / presentation の4層とし、依存方向ルール（domain層は何にも依存しない）を厳守
2. **実装はテスト駆動開発（TDD）に従う**（[.claude/guides/tdd.md](.claude/guides/tdd.md)）
   - テストコードを書いてから実装コードを書く（逆順禁止）
   - 各タスクで Red（失敗確認）→ Green（実装）→ Refactor のサイクルを厳守
   - テスト実行は `uv run pytest` を使用

## ディレクトリ構成

```
.
├── CLAUDE.md                  # プロジェクトメモリ（開発原則・プロセスの定義）
├── pyproject.toml             # プロジェクト定義（uv workspace・pytest・ruff）
├── docs/                      # 永続的ドキュメント（アプリ全体の「何を作るか」）
│   └── ideas/                 # 壁打ち・ブレストの下書き（/setup-project の入力）
├── src/                       # アプリケーション本体のソースコード（開発対象のみ）
├── tests/                     # アプリケーション本体のテストコード
├── tools/
│   └── dashboard/             # プロジェクト状況ダッシュボード生成ツール（独立パッケージ）
│       ├── pyproject.toml     # project-dashboard パッケージ定義（dashboardコマンド）
│       ├── src/project_dashboard/  # DDD 4層構造の実装
│       └── tests/             # ダッシュボードのテスト（unit / integration）
├── .steering/                 # 作業単位のドキュメント（「今回何をするか」の計画・進捗）
└── .claude/
    ├── commands/              # スラッシュコマンド（/setup-project, /add-feature, /review-docs）
    ├── skills/                # スキル（各種ドキュメント作成・steering管理）
    ├── agents/                # サブエージェント（doc-reviewer, implementation-validator）
    └── guides/                # 設計・実装ガイド（ddd.md, tdd.md）
```

### 永続的ドキュメント（`docs/`）

アプリケーション全体の「何を作るか」「どう作るか」を定義する、プロジェクトの北極星となるドキュメント群です。頻繁には更新されません。

| ドキュメント | 内容 |
|---|---|
| `product-requirements.md` | プロダクト要求定義書（PRD） |
| `functional-design.md` | 機能設計書 |
| `architecture.md` | 技術仕様書（アーキテクチャ設計書） |
| `repository-structure.md` | リポジトリ構造定義書 |
| `development-guidelines.md` | 開発ガイドライン |
| `glossary.md` | 用語集（ユビキタス言語定義） |

`docs/ideas/` にはブレスト・壁打ちの下書きメモを置きます。`/setup-project` 実行時に自動的に読み込まれ、PRD作成の材料になります。

### 作業単位のドキュメント（`.steering/`）

特定の機能追加・変更作業ごとに `.steering/[YYYYMMDD]-[タスク名]/` 形式で作成される、その作業に閉じた計画・進捗ドキュメントです。

- `requirements.md`: 今回の作業の要求内容
- `design.md`: 変更内容の設計（ドメインモデルを含む）
- `tasklist.md`: 具体的なタスクリスト（TDDサイクル単位で管理）

## 使い方

### 初回セットアップ

1. `docs/ideas/` にアイデアメモを書く（任意。書かなければ対話形式でヒアリングされます）
2. `/setup-project` を実行し、6つの永続ドキュメントを対話的に作成する

```bash
claude
> /setup-project
```

PRD（`product-requirements.md`）作成後はユーザーの承認を得てから次に進み、以降のドキュメントは自動生成されます。

### 日常的な使い方

基本は通常の会話でClaude Codeに依頼してください。

```
> PRDに新機能を追加してください
> architecture.mdのパフォーマンス要件を見直して
> glossary.mdに新しいドメイン用語を追加して
```

### 機能追加

`/add-feature [機能名]` を実行すると、計画（ステアリングファイル作成）→ TDD実装 → コードレビュー → テスト実行 → 振り返りまでを、ユーザーの介入なしに一気通貫で自動実行します。

```bash
> /add-feature ユーザープロフィール編集
```

処理の流れ（[.claude/commands/add-feature.md](.claude/commands/add-feature.md)）:

1. `.steering/[日付]-[機能名]/` を作成し、`requirements.md` / `design.md` / `tasklist.md` を用意
2. `CLAUDE.md` と `docs/` の永続ドキュメント、`ddd.md` / `tdd.md` を読み込んでプロジェクト方針を理解
3. `src/` の既存実装パターンを調査
4. `steering` スキル（計画モード）でステアリングファイルを生成し、`doc-reviewer` サブエージェントでレビュー
5. `tasklist.md` の全タスクが完了するまで、TDD（RED → GREEN → REFACTOR）サイクルで実装をループ
6. `implementation-validator` サブエージェントで実装品質・DDD/TDD準拠を検証
7. `uv run pytest` / `uv run pytest --cov=src` / `uv run ruff check .` / `uv run ruff format --check .` を実行
8. `steering` スキル（振り返りモード）で `tasklist.md` に振り返りを記録し、必要に応じて `docs/` を更新

### ドキュメントレビュー

作成済みのドキュメントについて、`doc-reviewer` サブエージェントによる詳細レビューを個別に実行できます。

```bash
> /review-docs docs/product-requirements.md
```

完全性・具体性・一貫性・測定可能性の観点でレビューし、優先度別（高/中/低）の改善点を報告します。

## スキル一覧

`.claude/skills/` 配下にあり、上記コマンドから必要に応じて自動的にロードされます。

| スキル | 用途 |
|---|---|
| `prd-writing` | プロダクト要求定義書の作成 |
| `functional-design` | 機能設計書の作成 |
| `architecture-design` | アーキテクチャ設計書の作成（DDD準拠） |
| `repository-structure` | リポジトリ構造定義書の作成 |
| `development-guidelines` | 開発ガイドラインの作成 |
| `glossary-creation` | 用語集の作成 |
| `steering` | ステアリングファイルの作成・実装進捗管理・振り返り記録 |

## サブエージェント一覧

| エージェント | 用途 |
|---|---|
| `doc-reviewer` | ドキュメント（永続ドキュメント・ステアリングファイル）の品質レビュー |
| `implementation-validator` | 実装コードの品質・DDD/TDD準拠の検証 |

## テスト

```bash
uv run pytest                  # テスト実行
uv run pytest --cov=src        # カバレッジ計測（80%以上を維持）
uv run ruff check .            # Lint
uv run ruff format --check .   # フォーマットチェック
```

## ライセンス

[LICENSE](LICENSE) を参照してください。
