# ドメイン駆動設計（DDD）ガイド

**このプロジェクトの設計は必ずドメイン駆動設計（DDD）に従う。**

このガイドは設計時（アーキテクチャ設計、機能設計、ステアリングファイルのdesign.md作成時）に必ず読み込み、記載されたルールに従うこと。

**既存コードの修正時**は、最低限「6. コード修正時の注意点」を読み、それに従うこと。

## 適用ルール（MUST / NEVER）

**MUST（必須）**:
- 設計を始める前に `docs/glossary.md`（ユビキタス言語定義）を確認し、用語をコード・ドキュメント全体で統一する
- すべての設計ドキュメントにドメインモデル（エンティティ・値オブジェクト・集約）を明記する
- レイヤー構造は本ガイドの4層構造（domain / application / infrastructure / presentation）に従う
- ドメイン層は他のどの層にも依存させない（依存方向ルールを厳守）
- ビジネスルールは必ずドメイン層（エンティティ・値オブジェクト・ドメインサービス）に置く

**NEVER（禁止）**:
- ドメイン層からインフラ層・プレゼンテーション層をimportする
- ビジネスルールをアプリケーションサービスやUIに書く（ドメインモデル貧血症）
- エンティティの属性を外部から直接書き換える設計にする（不変条件はエンティティ自身が守る）
- 集約をまたいでオブジェクトを直接参照する（他の集約はIDで参照する）
- ユビキタス言語にない独自用語をコードに導入する（必要なら先にglossary.mdに追加する）

## 1. 戦略的設計

### 1.1 ユビキタス言語

ドメインエキスパート（ユーザー）と開発者が同じ用語を使う。

- 用語は `docs/glossary.md` で定義し、**クラス名・メソッド名・変数名・テスト名にそのまま使う**
- 日本語用語には対応する英語名を必ず定義する（例: 注文 = Order、受注確定 = confirm_order）
- 同じ概念に複数の名前を使わない。別の名前が必要になったら境界づけられたコンテキストの分割を疑う

### 1.2 境界づけられたコンテキスト

- モデルが有効な範囲を明確にする。1つのコンテキスト内では用語の意味は一意
- コンテキストが複数ある場合は、コンテキストマップ（関係図）をarchitecture.mdに記載する
- 小規模プロジェクトでは単一コンテキストでよいが、その旨を明記する

## 2. レイヤー構造と依存方向ルール

### 4層構造

```
┌────────────────────────────────┐
│ presentation（プレゼンテーション層）│ CLI / API / UI
├────────────────────────────────┤
│ application（アプリケーション層）   │ ユースケースの調整役
├────────────────────────────────┤
│ domain（ドメイン層）★中心          │ エンティティ / 値オブジェクト /
│                                │ 集約 / ドメインサービス / リポジトリIF
├────────────────────────────────┤
│ infrastructure（インフラ層）       │ DB / ファイル / 外部API（リポジトリ実装）
└────────────────────────────────┘
```

### 依存方向ルール（最重要）

```
presentation → application → domain ← infrastructure
```

| 層 | 依存してよい層 | 責務 | 禁止事項 |
|----|--------------|------|---------|
| domain | なし（標準ライブラリのみ） | ビジネスルール、不変条件 | 他層のimport、DB・API・フレームワークへの依存 |
| application | domain | ユースケースの手順調整、トランザクション境界 | ビジネスルールの実装 |
| infrastructure | domain | リポジトリインターフェースの実装、技術詳細 | ビジネスルールの実装 |
| presentation | application | 入力受付、バリデーション（形式）、表示 | ドメイン層の直接操作、ビジネスルール |

**依存性逆転**: リポジトリの**インターフェースはdomain層**に定義し、**実装はinfrastructure層**に置く。

### ディレクトリ構造（Python標準形）

```
src/
└── {パッケージ名}/
    ├── domain/
    │   ├── models/          # エンティティ・値オブジェクト・集約
    │   ├── services/        # ドメインサービス
    │   ├── exceptions.py    # ドメイン例外（DomainError等）
    │   └── repositories/    # リポジトリインターフェース（抽象）
    ├── application/
    │   └── usecases/        # ユースケース（アプリケーションサービス）
    ├── infrastructure/
    │   └── repositories/    # リポジトリ実装
    └── presentation/        # CLI / API エンドポイント
tests/
    ├── unit/
    │   ├── domain/          # ドメイン層のテスト（最重要・最多）
    │   └── application/
    └── integration/
```

## 3. 戦術的設計（Pythonコード例付き）

### 3.1 値オブジェクト（Value Object）

**同一性ではなく値で等価性が決まる、不変のオブジェクト。**

- `@dataclass(frozen=True)` で実装する
- 生成時（`__post_init__`）にバリデーションし、不正な値オブジェクトの存在を許さない
- プリミティブ型（str, int）をそのままドメインの概念に使わない（プリミティブ執着の回避）

```python
# ✅ 良い例
from dataclasses import dataclass

@dataclass(frozen=True)
class Money:
    amount: int
    currency: str = "JPY"

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("金額は0以上でなければならない")

    def add(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("通貨単位が異なる金額は加算できない")
        return Money(self.amount + other.amount, self.currency)

# ❌ 悪い例: intをそのまま使い、負の金額チェックが利用側に散らばる
def calculate_total(price: int, quantity: int) -> int: ...
```

### 3.2 エンティティ（Entity）

**IDによって同一性が決まり、ライフサイクルを持つオブジェクト。**

- 不変条件（ビジネスルール）はエンティティ自身のメソッドで守る
- 状態変更は意図を表すメソッド経由でのみ行う（セッターの公開禁止）
- ビジネスルール違反はドメイン例外で表現する。ドメイン例外は `domain/exceptions.py` に定義する:

```python
# domain/exceptions.py
class DomainError(Exception):
    """ビジネスルール違反を表す基底例外"""
```

```python
# ✅ 良い例: 状態遷移ルールをエンティティ自身が守る
from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID, uuid4

class OrderStatus(Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"

@dataclass
class Order:
    id: UUID = field(default_factory=uuid4)
    status: OrderStatus = OrderStatus.DRAFT
    lines: list["OrderLine"] = field(default_factory=list)

    def confirm(self) -> None:
        if not self.lines:
            raise DomainError("明細のない注文は確定できない")
        if self.status is not OrderStatus.DRAFT:
            raise DomainError("下書き状態の注文のみ確定できる")
        self.status = OrderStatus.CONFIRMED

# ❌ 悪い例: 利用側が直接状態を書き換える（ルールが守られる保証がない）
order.status = OrderStatus.CONFIRMED
```

### 3.3 集約（Aggregate）

**整合性を保つ単位。集約ルート経由でのみ内部を変更する。**

- 集約ルート（例: Order）が内部オブジェクト（例: OrderLine）への変更を仲介する
- **他の集約はIDで参照する**（オブジェクト参照しない）
- 1トランザクション = 1集約の更新を原則とする

```python
# ✅ 良い例: 他の集約(Customer)はIDで参照
@dataclass
class Order:
    customer_id: UUID  # Customerオブジェクトを持たない
    ...

# ❌ 悪い例: 他の集約を直接保持（整合性境界が曖昧になる）
@dataclass
class Order:
    customer: Customer
    ...
```

### 3.4 ドメインサービス

**単一のエンティティ・値オブジェクトに属さないビジネスルール**のみをドメインサービスにする。

```python
# ✅ 良い例: 複数の集約にまたがる判定
class DuplicateOrderChecker:
    def __init__(self, order_repository: OrderRepository) -> None:
        self._order_repository = order_repository

    def is_duplicate(self, order: Order) -> bool: ...
```

**注意**: 安易にサービスを作らない。ロジックの置き場所は「エンティティ → 値オブジェクト → ドメインサービス」の優先順で検討する。

### 3.5 リポジトリ

- インターフェース（抽象基底クラス）は **domain層** に定義
- 実装は **infrastructure層** に配置
- 集約単位で作る（OrderLineRepositoryは作らない。Orderの集約ルート経由）

```python
# domain/repositories/order_repository.py
from abc import ABC, abstractmethod

class OrderRepository(ABC):
    @abstractmethod
    def find_by_id(self, order_id: UUID) -> Order | None: ...

    @abstractmethod
    def save(self, order: Order) -> None: ...

# infrastructure/repositories/json_order_repository.py
class JsonOrderRepository(OrderRepository):
    """JSONファイルによる実装（技術詳細はここに閉じ込める）"""
    ...
```

### 3.6 アプリケーションサービス（ユースケース）

- 手順の調整のみを行い、**ビジネスルールを書かない**
- 1ユースケース = 1クラス（または1メソッド）

```python
# ✅ 良い例: 調整のみ。ルールはOrder.confirm()の中にある
class ConfirmOrderUseCase:
    def __init__(self, order_repository: OrderRepository) -> None:
        self._order_repository = order_repository

    def execute(self, order_id: UUID) -> None:
        order = self._order_repository.find_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(order_id)
        order.confirm()          # ← ビジネスルールはドメイン層
        self._order_repository.save(order)

# ❌ 悪い例: ユースケースにビジネスルールが漏れている
class ConfirmOrderUseCase:
    def execute(self, order_id: UUID) -> None:
        order = self._order_repository.find_by_id(order_id)
        if not order.lines:                    # ❌ ドメインルールの漏出
            raise DomainError(...)
        order.status = OrderStatus.CONFIRMED   # ❌ 直接書き換え
```

## 4. 設計ドキュメントに必ず含める内容

design.md / architecture.md / functional-design.md には以下を記載する:

1. **ドメインモデル表**: エンティティ / 値オブジェクト / 集約の一覧と責務・不変条件
2. **集約境界**: どのオブジェクトがどの集約に属するか、集約間の参照（ID参照）
3. **リポジトリ一覧**: 集約ルートごとのインターフェース定義
4. **ユースケース一覧**: アプリケーションサービスとして実装する操作
5. **レイヤー配置**: 新規ファイルがどの層のどのディレクトリに入るか

## 5. 設計時チェックリスト

設計完了前に必ず自己検証すること:

- [ ] 用語はglossary.md（ユビキタス言語）と一致しているか？
- [ ] エンティティと値オブジェクトを区別したか？（IDで識別→エンティティ、値で等価→値オブジェクト）
- [ ] 値オブジェクトは不変（frozen）で、生成時バリデーションがあるか？
- [ ] ビジネスルール・不変条件はドメイン層に置かれているか？
- [ ] 集約境界が定義され、他の集約はID参照になっているか？
- [ ] リポジトリのインターフェースはdomain層、実装はinfrastructure層か？
- [ ] 依存方向は presentation → application → domain ← infrastructure になっているか？
- [ ] ドメイン層が標準ライブラリ以外に依存していないか？
- [ ] アプリケーションサービスにビジネスルールが漏れていないか？

## 6. コード修正時の注意点

既存コードを修正するとき（バグ修正・機能変更・リファクタリング）は、新規設計時のルールに加えて以下を守ること:

- **ユビキタス言語を守る**: コードの命名と業務用語を一致させる。業務用語が変わったら命名も追従させる（glossary.mdの更新とコードのリネームをセットで行う）
- **コンテキスト境界を侵食しない**: 他コンテキストのクラスを直接参照しない。連携は腐敗防止層や公開インターフェース経由で行う
- **集約の不変条件を壊さない**: 集約ルートを経由して操作する。集約境界の変更はトランザクション整合性への影響を確認する
- **レイヤー分離を維持する**: ドメイン層にSQL・フレームワーク・UI都合のコードを混入させない
- **ドメインロジックの流出を防ぐ**: 業務上の判断・計算はサービス層やUIではなくドメインオブジェクトに寄せる
- **設計意図を理解してから修正する**: 一見冗長な構造にも理由がある。不変条件のテストやドメインエキスパートへの確認を先に行う
- **必要ならモデル自体を見直す**: 業務理解の深化でモデルが現実に合わなくなったら、パッチではなくモデルのリファクタリングを検討する
