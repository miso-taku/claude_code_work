"""リポジトリ→ユースケース→レンダラーの結合動作を確認する統合テスト。"""

from pathlib import Path

from project_dashboard.application.usecases.get_project_status import GetProjectStatusUseCase
from project_dashboard.infrastructure.repositories.filesystem_project_status_repository import (
    FilesystemProjectStatusRepository,
)
from project_dashboard.presentation.html_renderer import render_dashboard


def fake_git_runner(args: list[str]) -> str:
    if args[0] == "log":
        return "61dc097|2026-07-06|DDD, TDD対応\n"
    if args[0] == "status":
        return ""
    if args[0] == "rev-parse":
        return "main\n"
    raise AssertionError(f"想定外のgitコマンド: {args}")


def test_リポジトリ構造からダッシュボードHTMLが生成される(tmp_path: Path) -> None:
    # Arrange: docs 一部あり・steering 1件・src ありのリポジトリ構造を作る
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "glossary.md").write_text("# 用語集", encoding="utf-8")
    steering = tmp_path / ".steering" / "20260707-sample"
    steering.mkdir(parents=True)
    (steering / "tasklist.md").write_text(
        "\n".join(["## フェーズ1: 作業", "- [x] タスクA", "- [ ] タスクB"]),
        encoding="utf-8",
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")

    # Act
    repository = FilesystemProjectStatusRepository(root=tmp_path, run_git=fake_git_runner)
    status = GetProjectStatusUseCase(repository=repository).execute()
    html = render_dashboard(status, generated_on="2026-07-07")

    # Assert: 集計値がHTMLに反映されている
    assert tmp_path.name in html
    assert "main" in html
    assert "DDD, TDD対応" in html
    assert "20260707-sample" in html
    assert "2026-07-07" in html
    assert 'data-stage="documentation"' in html
