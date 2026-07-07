"""プロジェクト状況（ProjectStatus集約）のドメインモデル。

用語は .steering/20260707-project-dashboard/design.md のユビキタス言語表に従う。
"""

from dataclasses import dataclass, field
from enum import Enum


class RoadmapStage(Enum):
    """ロードマップ段階。スペック駆動開発の3段階を表す値オブジェクト。

    TEMPLATE（テンプレート整備）は本テンプレート自体の整備がすでに完了しているため、
    常に完了済みの過去段階として扱う（design.md「主要なビジネスルール」参照）。
    現在地は DOCUMENTATION / IMPLEMENTATION のいずれかになる。
    """

    TEMPLATE = "template"
    DOCUMENTATION = "documentation"
    IMPLEMENTATION = "implementation"


@dataclass(frozen=True)
class TaskProgress:
    """タスク進捗。tasklist.md のチェックボックス完了数/総数を表す値オブジェクト。

    不変条件: 0 <= done <= total
    """

    done: int
    total: int

    def __post_init__(self) -> None:
        if self.total < 0:
            raise ValueError("タスク総数は0以上でなければならない")
        if self.done < 0:
            raise ValueError("完了数は0以上でなければならない")
        if self.done > self.total:
            raise ValueError("完了数はタスク総数を超えられない")

    @property
    def percent(self) -> int:
        """完了率（0-100の整数）。総数0のときは0。"""
        if self.total == 0:
            return 0
        return round(self.done / self.total * 100)


@dataclass(frozen=True)
class Commit:
    """コミット。gitの1コミットを表す値オブジェクト。"""

    hash: str
    date: str
    subject: str

    def __post_init__(self) -> None:
        if not self.hash:
            raise ValueError("コミットハッシュは空にできない")


@dataclass(frozen=True)
class DocumentStatus:
    """ドキュメント状況。正式ドキュメント1点の存在有無を表す値オブジェクト。"""

    name: str
    description: str
    exists: bool

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("ドキュメント名は空にできない")


@dataclass(frozen=True)
class SourceStats:
    """ソース統計。Pythonファイル数・行数を表す値オブジェクト。

    不変条件: ファイル数・行数は0以上
    """

    file_count: int
    line_count: int

    def __post_init__(self) -> None:
        if self.file_count < 0:
            raise ValueError("ファイル数は0以上でなければならない")
        if self.line_count < 0:
            raise ValueError("行数は0以上でなければならない")


@dataclass(frozen=True)
class PhaseProgress:
    """フェーズ進捗。tasklist.md の「## フェーズN」単位の進捗を表す値オブジェクト。"""

    name: str
    progress: TaskProgress

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("フェーズ名は空にできない")


@dataclass
class SteeringWork:
    """ステアリング作業。`.steering/[日付]-[名前]/` 1ディレクトリに対応するエンティティ。

    ディレクトリ名（name）がIDとして同一性を決める。
    """

    name: str
    progress: TaskProgress
    phases: list[PhaseProgress] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("ステアリング作業名は空にできない")

    @property
    def is_completed(self) -> bool:
        """完了判定。タスクが1件以上あり、すべて完了しているときのみ完了。"""
        return self.progress.total > 0 and self.progress.done == self.progress.total


@dataclass
class ProjectStatus:
    """プロジェクト状況。ある時点のリポジトリ全体の状態を表す集約ルート。

    内部オブジェクト（コミット・ドキュメント状況・ステアリング作業等）へは
    必ずこの集約ルート経由でアクセスする。
    """

    project_name: str
    branch: str
    is_clean: bool
    commits: list[Commit] = field(default_factory=list)
    documents: list[DocumentStatus] = field(default_factory=list)
    steerings: list[SteeringWork] = field(default_factory=list)
    source_stats: SourceStats = SourceStats(file_count=0, line_count=0)
    tests_stats: SourceStats = SourceStats(file_count=0, line_count=0)

    @property
    def documents_progress(self) -> TaskProgress:
        """正式ドキュメントの整備進捗（存在する点数/全点数）。"""
        done = sum(1 for doc in self.documents if doc.exists)
        return TaskProgress(done=done, total=len(self.documents))

    @property
    def current_stage(self) -> RoadmapStage:
        """現在のロードマップ段階の判定（ビジネスルール）。

        正式ドキュメントが1点でも欠けていれば、src/ に実装コードが存在していても
        DOCUMENTATION 段階とする（ドキュメント未整備のまま実装が先行しているケースを
        許容するため）。全点揃ってはじめて IMPLEMENTATION 段階に進む。
        """
        all_documents_exist = len(self.documents) > 0 and all(doc.exists for doc in self.documents)
        if not all_documents_exist:
            return RoadmapStage.DOCUMENTATION
        return RoadmapStage.IMPLEMENTATION

    @property
    def completed_steering_count(self) -> int:
        """完了したステアリング作業の数。"""
        return sum(1 for work in self.steerings if work.is_completed)
