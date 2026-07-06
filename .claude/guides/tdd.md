# テスト駆動開発（TDD）ガイド

**このプロジェクトの実装は必ずテスト駆動開発（TDD）に従う。テストコードを書いてから実装コードを書く。**

このガイドは実装時（steeringモード2、/add-featureの実装ループ）に必ず読み込み、記載された手順に従うこと。

## 適用ルール（MUST / NEVER）

**MUST（必須）**:
- 実装コードを書く前に、必ずテストコードを先に書く
- テストを書いたら**実装前に必ず実行し、失敗（RED）を確認する**
- 実装後にテストを実行し、成功（GREEN）を確認してから次に進む
- 1つのRed-Green-Refactorサイクルは小さく保つ（1振る舞い単位）
- テストは `tests/` 配下に、実装と対応するパス構造で配置する

**NEVER（禁止）**:
- 実装コードを先に書いてから、後付けでテストを書く
- テストの失敗確認（RED）をスキップして実装に進む
- テストが失敗したまま次のタスクに進む
- 失敗するテストを通すために、テスト側を安易に弱める（アサーション削除・skip付与）
- 「テストは後でまとめて書く」と宣言してタスクを進める

## Red-Green-Refactorサイクル（厳密な手順）

**1タスク（1振る舞い）ごとに以下の5ステップを順番に実行する。ステップの省略・入れ替えは禁止。**

### ステップ1: RED — テストを書く

対象の振る舞いを検証するテストを書く。この時点で実装コードは存在しなくてよい。

```python
# tests/unit/domain/models/test_order.py
def test_明細のない注文は確定できない() -> None:
    order = Order()

    with pytest.raises(DomainError):
        order.confirm()
```

### ステップ2: RED確認 — テストを実行して失敗を確認する（省略禁止）

```bash
uv run pytest tests/unit/domain/models/test_order.py -x
```

- **期待どおりの理由で失敗すること**を確認する（ImportError や構文エラーではなく、アサーション失敗または未実装による失敗）
- 失敗を確認せずに実装へ進むことは禁止。テストが最初から成功する場合、そのテストは何も検証していない可能性が高い — テストを見直す

### ステップ3: GREEN — テストを通す最小限の実装を書く

- テストを通すために必要な最小限のコードだけを書く
- テストされていない機能を先回りして実装しない（YAGNI）

### ステップ4: GREEN確認 — テストを実行して成功を確認する

```bash
uv run pytest tests/unit/domain/models/test_order.py -x
```

- 新しいテストが成功し、**既存のテストも全て成功している**ことを確認する

### ステップ5: REFACTOR — リファクタリング

- 重複除去、命名改善、構造整理を行う（振る舞いは変えない）
- リファクタリング後に再度テストを実行し、全テスト成功を確認する
- 改善点がなければスキップ可（このステップのみ省略可能）

## テストコードの書き方

### 基本構造: Arrange-Act-Assert（AAA）

```python
def test_確定済みの注文は再確定できない() -> None:
    # Arrange（準備）
    order = Order(lines=[OrderLine(product_id=uuid4(), quantity=1)])
    order.confirm()

    # Act & Assert（実行と検証）
    with pytest.raises(DomainError, match="下書き状態の注文のみ確定できる"):
        order.confirm()
```

### テスト命名

- テスト名は**日本語で振る舞いを記述する**（ユビキタス言語を使う）
- `test_{条件}の場合{結果}になる` の形式を推奨
- ❌ `test_confirm_2()` のような無意味な名前は禁止

### パラメタライズテスト（境界値・複数ケース）

```python
@pytest.mark.parametrize(
    ("amount", "expected_error"),
    [
        (-1, True),   # 境界値: 負数はエラー
        (0, False),   # 境界値: 0は許可
        (1, False),
    ],
)
def test_金額のバリデーション(amount: int, expected_error: bool) -> None:
    if expected_error:
        with pytest.raises(ValueError):
            Money(amount)
    else:
        assert Money(amount).amount == amount
```

### 必ずテストするケース

1. **正常系**: 代表的な成功パターン
2. **異常系**: ビジネスルール違反（ドメイン例外の発生）
3. **境界値**: 0、空リスト、最大値、None など

### テストの独立性

- 各テストは他のテストに依存せず、単独で実行可能にする
- 共有の可変状態を使わない。共通の準備は fixture を使う

```python
@pytest.fixture
def confirmed_order() -> Order:
    order = Order(lines=[OrderLine(product_id=uuid4(), quantity=1)])
    order.confirm()
    return order
```

### テストダブル（DDDとの連携）

- ユースケースのテストでは、リポジトリの**インターフェース（domain層の抽象）**に対するインメモリ実装（フェイク）を使う
- 外部I/O（DB・ファイル・API）に依存するユニットテストを書かない

```python
class InMemoryOrderRepository(OrderRepository):
    def __init__(self) -> None:
        self._orders: dict[UUID, Order] = {}

    def find_by_id(self, order_id: UUID) -> Order | None:
        return self._orders.get(order_id)

    def save(self, order: Order) -> None:
        self._orders[order.id] = order
```

## テストの配置とコマンド

### 配置ルール

実装ファイルとテストファイルは対応するパス構造にする:

| 実装 | テスト |
|------|--------|
| `src/{パッケージ名}/domain/models/order.py` | `tests/unit/domain/models/test_order.py` |
| `src/{パッケージ名}/application/usecases/confirm_order.py` | `tests/unit/application/usecases/test_confirm_order.py` |
| 複数レイヤー結合 | `tests/integration/test_{シナリオ}.py` |

### 標準コマンド（Python + uv）

```bash
uv run pytest                        # 全テスト実行
uv run pytest {対象ファイル} -x       # 対象テストのみ・最初の失敗で停止
uv run pytest --cov=src              # カバレッジ計測
uv run ruff check .                  # リント
uv run ruff format --check .         # フォーマット確認
uv run mypy src                      # 型チェック（導入している場合）
```

※ プロジェクトに `docs/development-guidelines.md` がある場合はそちらのコマンド定義を優先する。

## カバレッジ基準

- **ユニットテストカバレッジ: 80%以上**（ドメイン層は90%以上を目標）
- カバレッジは「結果」であり「目的」ではない。数字合わせのための無意味なテストを書かない

## tasklist.mdとの連携

tasklist.mdの実装タスクは、必ずTDDサイクルをサブタスクとして含む形式で書く:

```markdown
- [ ] Order エンティティの confirm() を実装
  - [ ] RED: test_order.py にテストを作成し、失敗を確認
  - [ ] GREEN: confirm() を実装し、テスト成功を確認
  - [ ] REFACTOR: リファクタリングと全テスト成功確認
```

## 実装時チェックリスト

各タスク完了前に必ず自己検証すること:

- [ ] テストコードを実装コードより先に書いたか？
- [ ] 実装前にテストを実行し、期待どおりの理由で失敗することを確認したか？
- [ ] 実装後にテストを実行し、新規・既存の全テストが成功したか？
- [ ] 正常系・異常系・境界値をテストしたか？
- [ ] テスト名は日本語で振る舞いを表しているか？
- [ ] テストは独立して実行可能か？（実行順序に依存していないか）
- [ ] ユニットテストが外部I/Oに依存していないか？
