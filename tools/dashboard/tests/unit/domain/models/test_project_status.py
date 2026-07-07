"""ドメインモデル（domain/models/project_status.py）のユニットテスト。"""

import dataclasses

import pytest

from project_dashboard.domain.exceptions import DomainError
from project_dashboard.domain.models.project_status import (
    Commit,
    DocumentStatus,
    PhaseProgress,
    ProjectStatus,
    RoadmapStage,
    SourceStats,
    SteeringWork,
    TaskProgress,
)


def _make_documents(exists_count: int) -> list[DocumentStatus]:
    """正式ドキュメント6点のうち先頭 exists_count 点だけ存在する状態を作る。"""
    names = [
        "product-requirements.md",
        "functional-design.md",
        "architecture.md",
        "repository-structure.md",
        "development-guidelines.md",
        "glossary.md",
    ]
    return [
        DocumentStatus(name=name, description="説明", exists=i < exists_count)
        for i, name in enumerate(names)
    ]


def _make_status(
    documents: list[DocumentStatus],
    source_stats: SourceStats | None = None,
) -> ProjectStatus:
    if source_stats is None:
        source_stats = SourceStats(file_count=0, line_count=0)
    return ProjectStatus(
        project_name="claude_code_work",
        branch="main",
        is_clean=True,
        commits=[Commit(hash="abc1234", date="2026-07-06", subject="件名")],
        documents=documents,
        steerings=[],
        source_stats=source_stats,
        tests_stats=SourceStats(file_count=0, line_count=0),
    )


class TestDomainError:
    def test_ビジネスルール違反の基底例外として送出できる(self) -> None:
        with pytest.raises(DomainError, match="ビジネスルール違反"):
            raise DomainError("ビジネスルール違反")


class TestTaskProgress:
    def test_完了数と総数を保持できる(self) -> None:
        progress = TaskProgress(done=3, total=10)

        assert progress.done == 3
        assert progress.total == 10

    def test_完了率をパーセント整数で算出できる(self) -> None:
        assert TaskProgress(done=1, total=4).percent == 25

    def test_総数0の場合完了率は0になる(self) -> None:
        assert TaskProgress(done=0, total=0).percent == 0

    @pytest.mark.parametrize(
        ("done", "total"),
        [
            (-1, 5),  # 境界値: 完了数が負
            (6, 5),  # 完了数 > 総数
            (0, -1),  # 総数が負
        ],
    )
    def test_不正な進捗は生成できない(self, done: int, total: int) -> None:
        with pytest.raises(ValueError):
            TaskProgress(done=done, total=total)

    def test_境界値_完了数0と完了数イコール総数は許可される(self) -> None:
        assert TaskProgress(done=0, total=5).percent == 0
        assert TaskProgress(done=5, total=5).percent == 100

    def test_値で等価比較される(self) -> None:
        assert TaskProgress(done=1, total=2) == TaskProgress(done=1, total=2)

    def test_不変であり属性を書き換えられない(self) -> None:
        progress = TaskProgress(done=1, total=2)

        with pytest.raises(dataclasses.FrozenInstanceError):
            progress.done = 5  # type: ignore[misc]


class TestCommit:
    def test_ハッシュと日付とサブジェクトを保持できる(self) -> None:
        commit = Commit(hash="61dc097", date="2026-07-06", subject="DDD, TDD対応")

        assert commit.hash == "61dc097"
        assert commit.date == "2026-07-06"
        assert commit.subject == "DDD, TDD対応"

    def test_ハッシュが空文字の場合生成できない(self) -> None:
        with pytest.raises(ValueError):
            Commit(hash="", date="2026-07-06", subject="件名")

    def test_サブジェクトは空文字でも許可される(self) -> None:
        commit = Commit(hash="abc1234", date="2026-07-06", subject="")

        assert commit.subject == ""


class TestDocumentStatus:
    def test_名前と説明と存在有無を保持できる(self) -> None:
        doc = DocumentStatus(name="glossary.md", description="用語集", exists=True)

        assert doc.name == "glossary.md"
        assert doc.description == "用語集"
        assert doc.exists is True

    def test_名前が空文字の場合生成できない(self) -> None:
        with pytest.raises(ValueError):
            DocumentStatus(name="", description="説明", exists=False)


class TestSourceStats:
    def test_ファイル数と行数を保持できる(self) -> None:
        stats = SourceStats(file_count=3, line_count=120)

        assert stats.file_count == 3
        assert stats.line_count == 120

    @pytest.mark.parametrize(
        ("file_count", "line_count"),
        [
            (-1, 0),  # 境界値: ファイル数が負
            (0, -1),  # 境界値: 行数が負
        ],
    )
    def test_負の値では生成できない(self, file_count: int, line_count: int) -> None:
        with pytest.raises(ValueError):
            SourceStats(file_count=file_count, line_count=line_count)

    def test_境界値_ゼロは許可される(self) -> None:
        stats = SourceStats(file_count=0, line_count=0)

        assert stats.file_count == 0


class TestPhaseProgress:
    def test_フェーズ名と進捗を保持できる(self) -> None:
        phase = PhaseProgress(
            name="フェーズ1: 開発環境整備", progress=TaskProgress(done=1, total=3)
        )

        assert phase.name == "フェーズ1: 開発環境整備"
        assert phase.progress.percent == 33

    def test_フェーズ名が空文字の場合生成できない(self) -> None:
        with pytest.raises(ValueError):
            PhaseProgress(name="", progress=TaskProgress(done=0, total=0))


class TestSteeringWork:
    def test_名前と進捗とフェーズ別進捗を保持できる(self) -> None:
        work = SteeringWork(
            name="20260706-integrate-ddd-tdd",
            progress=TaskProgress(done=32, total=32),
            phases=[PhaseProgress(name="フェーズ1", progress=TaskProgress(done=9, total=9))],
        )

        assert work.name == "20260706-integrate-ddd-tdd"
        assert work.progress.percent == 100
        assert len(work.phases) == 1

    def test_全タスク完了の場合は完了と判定される(self) -> None:
        work = SteeringWork(name="20260706-a", progress=TaskProgress(done=5, total=5), phases=[])

        assert work.is_completed is True

    def test_未完了タスクが残る場合は完了と判定されない(self) -> None:
        work = SteeringWork(name="20260706-a", progress=TaskProgress(done=4, total=5), phases=[])

        assert work.is_completed is False

    def test_境界値_タスク総数0の場合は完了と判定されない(self) -> None:
        work = SteeringWork(name="20260706-a", progress=TaskProgress(done=0, total=0), phases=[])

        assert work.is_completed is False

    def test_名前が空文字の場合生成できない(self) -> None:
        with pytest.raises(ValueError):
            SteeringWork(name="", progress=TaskProgress(done=0, total=0), phases=[])


class TestProjectStatus:
    def test_ドキュメント進捗を算出できる(self) -> None:
        status = _make_status(documents=_make_documents(exists_count=2))

        assert status.documents_progress == TaskProgress(done=2, total=6)

    def test_境界値_ドキュメントリストが空でも進捗を算出できる(self) -> None:
        status = _make_status(documents=[])

        assert status.documents_progress == TaskProgress(done=0, total=0)

    def test_ドキュメントが6点未満の場合はドキュメント作成段階と判定される(self) -> None:
        status = _make_status(documents=_make_documents(exists_count=5))

        assert status.current_stage is RoadmapStage.DOCUMENTATION

    def test_ドキュメントが1点もない場合もドキュメント作成段階と判定される(self) -> None:
        status = _make_status(documents=_make_documents(exists_count=0))

        assert status.current_stage is RoadmapStage.DOCUMENTATION

    def test_実装コードがあってもドキュメント未整備なら文書作成段階と判定される(self) -> None:
        status = _make_status(
            documents=_make_documents(exists_count=3),
            source_stats=SourceStats(file_count=10, line_count=500),
        )

        assert status.current_stage is RoadmapStage.DOCUMENTATION

    def test_ドキュメントが全て揃うと実装段階と判定される(self) -> None:
        status = _make_status(documents=_make_documents(exists_count=6))

        assert status.current_stage is RoadmapStage.IMPLEMENTATION

    def test_完了したステアリング作業数を数えられる(self) -> None:
        status = _make_status(documents=[])
        status.steerings = [
            SteeringWork(name="20260706-a", progress=TaskProgress(done=3, total=3), phases=[]),
            SteeringWork(name="20260707-b", progress=TaskProgress(done=1, total=3), phases=[]),
        ]

        assert status.completed_steering_count == 1
