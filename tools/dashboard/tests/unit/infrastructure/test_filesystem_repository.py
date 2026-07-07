"""FilesystemProjectStatusRepository のユニットテスト。

git はフェイクの実行関数を注入し、外部プロセスに依存しない。
"""

from pathlib import Path

from project_dashboard.domain.models.project_status import RoadmapStage
from project_dashboard.infrastructure.repositories.filesystem_project_status_repository import (
    FilesystemProjectStatusRepository,
)


def fake_git_runner(args: list[str]) -> str:
    """通常ケースの git 出力を返すフェイク。"""
    if args[0] == "log":
        return "61dc097|2026-07-06|DDD, TDD対応\n7751c90|2026-03-20|最初のコミット\n"
    if args[0] == "status":
        return ""
    if args[0] == "rev-parse":
        return "main\n"
    raise AssertionError(f"想定外のgitコマンド: {args}")


def failing_git_runner(args: list[str]) -> str:
    """git が利用できない環境を模したフェイク。"""
    raise OSError("git: command not found")


def _build_normal_repo(root: Path) -> None:
    """docs 一部あり・steering 2件・src ありの通常ケースを構築する。"""
    (root / "docs").mkdir()
    (root / "docs" / "product-requirements.md").write_text("# PRD", encoding="utf-8")
    (root / "docs" / "glossary.md").write_text("# 用語集", encoding="utf-8")

    steering_a = root / ".steering" / "20260706-integrate-ddd-tdd"
    steering_a.mkdir(parents=True)
    (steering_a / "tasklist.md").write_text(
        "\n".join(["## フェーズ1: 作業", "- [x] タスクA", "- [x] タスクB"]),
        encoding="utf-8",
    )
    steering_b = root / ".steering" / "20260707-dashboard"
    steering_b.mkdir()
    (steering_b / "tasklist.md").write_text(
        "\n".join(["## フェーズ1: 作業", "- [x] タスクA", "- [ ] タスクB"]),
        encoding="utf-8",
    )

    (root / "src" / "pkg").mkdir(parents=True)
    (root / "src" / "pkg" / "main.py").write_text("print('hi')\nx = 1\n", encoding="utf-8")
    (root / "tests").mkdir()
    (root / "tests" / "test_main.py").write_text("def test_a(): pass\n", encoding="utf-8")


class TestFilesystemProjectStatusRepositoryの通常ケース:
    def test_リポジトリ全体の状況を構築できる(self, tmp_path: Path) -> None:
        _build_normal_repo(tmp_path)
        repository = FilesystemProjectStatusRepository(root=tmp_path, run_git=fake_git_runner)

        status = repository.load()

        assert status.project_name == tmp_path.name
        assert status.branch == "main"
        assert status.is_clean is True
        assert len(status.commits) == 2
        assert status.documents_progress.done == 2
        assert status.documents_progress.total == 6
        assert status.current_stage is RoadmapStage.DOCUMENTATION
        assert len(status.steerings) == 2
        assert status.completed_steering_count == 1
        assert status.source_stats.file_count == 1
        assert status.source_stats.line_count == 2
        assert status.tests_stats.file_count == 1

    def test_ステアリング作業は新しい順に並ぶ(self, tmp_path: Path) -> None:
        _build_normal_repo(tmp_path)
        repository = FilesystemProjectStatusRepository(root=tmp_path, run_git=fake_git_runner)

        status = repository.load()

        assert status.steerings[0].name == "20260707-dashboard"
        assert status.steerings[1].name == "20260706-integrate-ddd-tdd"


class TestFilesystemProjectStatusRepositoryの異常系:
    def test_steeringディレクトリが空でもエラーにならない(self, tmp_path: Path) -> None:
        (tmp_path / ".steering").mkdir()
        repository = FilesystemProjectStatusRepository(root=tmp_path, run_git=fake_git_runner)

        status = repository.load()

        assert status.steerings == []

    def test_docsディレクトリが存在しなくてもエラーにならない(self, tmp_path: Path) -> None:
        repository = FilesystemProjectStatusRepository(root=tmp_path, run_git=fake_git_runner)

        status = repository.load()

        assert status.documents_progress.done == 0
        assert status.documents_progress.total == 6

    def test_tasklistのないsteeringディレクトリは進捗ゼロとして扱われる(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / ".steering" / "20260707-empty").mkdir(parents=True)
        repository = FilesystemProjectStatusRepository(root=tmp_path, run_git=fake_git_runner)

        status = repository.load()

        assert status.steerings[0].name == "20260707-empty"
        assert status.steerings[0].progress.total == 0
        assert status.steerings[0].is_completed is False

    def test_gitが失敗してもダッシュボード生成は継続できる(self, tmp_path: Path) -> None:
        repository = FilesystemProjectStatusRepository(root=tmp_path, run_git=failing_git_runner)

        status = repository.load()

        assert status.branch == "unknown"
        assert status.commits == []
        assert status.is_clean is True

    def test_steering直下のディレクトリでないファイルは無視される(self, tmp_path: Path) -> None:
        (tmp_path / ".steering").mkdir()
        (tmp_path / ".steering" / "README.md").write_text("メモ", encoding="utf-8")

        status = FilesystemProjectStatusRepository(root=tmp_path, run_git=fake_git_runner).load()

        assert status.steerings == []

    def test_境界値_ブランチ名が空の場合はunknownとして扱われる(self, tmp_path: Path) -> None:
        def empty_branch_runner(args: list[str]) -> str:
            if args[0] == "rev-parse":
                return "\n"
            return fake_git_runner(args)

        status = FilesystemProjectStatusRepository(
            root=tmp_path, run_git=empty_branch_runner
        ).load()

        assert status.branch == "unknown"
