"""html_renderer のユニットテスト。"""

from project_dashboard.domain.models.project_status import (
    Commit,
    DocumentStatus,
    PhaseProgress,
    ProjectStatus,
    SourceStats,
    SteeringWork,
    TaskProgress,
)
from project_dashboard.presentation.html_renderer import render_dashboard


def _make_status(**overrides: object) -> ProjectStatus:
    base: dict = {
        "project_name": "claude_code_work",
        "branch": "main",
        "is_clean": True,
        "commits": [Commit(hash="61dc097", date="2026-07-06", subject="DDD, TDD対応")],
        "documents": [
            DocumentStatus(name="product-requirements.md", description="PRD", exists=True),
            DocumentStatus(name="glossary.md", description="用語集", exists=False),
        ],
        "steerings": [
            SteeringWork(
                name="20260706-integrate-ddd-tdd",
                progress=TaskProgress(done=32, total=32),
                phases=[
                    PhaseProgress(name="フェーズ1: ガイド", progress=TaskProgress(done=9, total=9))
                ],
            )
        ],
        "source_stats": SourceStats(file_count=3, line_count=120),
        "tests_stats": SourceStats(file_count=2, line_count=80),
    }
    base.update(overrides)
    return ProjectStatus(**base)


class TestRenderDashboard:
    def test_集計値がHTMLに反映される(self) -> None:
        html = render_dashboard(_make_status(), generated_on="2026-07-07")

        assert "claude_code_work" in html
        assert "main" in html
        assert "61dc097" in html
        assert "DDD, TDD対応" in html
        assert "20260706-integrate-ddd-tdd" in html
        assert "glossary.md" in html
        assert "2026-07-07" in html

    def test_ドキュメント未整備の場合はドキュメント作成段階として表示される(self) -> None:
        html = render_dashboard(_make_status(), generated_on="2026-07-07")

        assert 'data-stage="documentation"' in html

    def test_ドキュメントが全て揃うと実装段階として表示される(self) -> None:
        documents = [
            DocumentStatus(name=f"doc{i}.md", description="説明", exists=True) for i in range(6)
        ]
        html = render_dashboard(_make_status(documents=documents), generated_on="2026-07-07")

        assert 'data-stage="implementation"' in html

    def test_HTML特殊文字がエスケープされる(self) -> None:
        commits = [Commit(hash="abc1234", date="2026-07-07", subject='<script>alert("x")</script>')]
        html = render_dashboard(_make_status(commits=commits), generated_on="2026-07-07")

        assert "<script>alert" not in html
        assert "&lt;script&gt;" in html

    def test_外部リソースへの参照を含まない(self) -> None:
        html = render_dashboard(_make_status(), generated_on="2026-07-07")

        assert "http://" not in html
        assert "https://" not in html

    def test_境界値_空のプロジェクトでも生成できる(self) -> None:
        status = ProjectStatus(project_name="empty", branch="unknown", is_clean=True)
        html = render_dashboard(status, generated_on="2026-07-07")

        assert "empty" in html
        assert "<!doctype html>" in html.lower()
