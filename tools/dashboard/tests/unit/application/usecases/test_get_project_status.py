"""GetProjectStatusUseCase のユニットテスト。

リポジトリはdomain層のインターフェースに対するインメモリのフェイクを使う。
"""

from project_dashboard.application.usecases.get_project_status import GetProjectStatusUseCase
from project_dashboard.domain.models.project_status import ProjectStatus
from project_dashboard.domain.repositories.project_status_repository import (
    ProjectStatusRepository,
)


class InMemoryProjectStatusRepository(ProjectStatusRepository):
    """テスト用のインメモリフェイク。"""

    def __init__(self, status: ProjectStatus) -> None:
        self._status = status

    def load(self) -> ProjectStatus:
        return self._status


class TestGetProjectStatusUseCase:
    def test_リポジトリから読み込んだプロジェクト状況を返す(self) -> None:
        status = ProjectStatus(project_name="demo", branch="main", is_clean=True)
        usecase = GetProjectStatusUseCase(repository=InMemoryProjectStatusRepository(status))

        result = usecase.execute()

        assert result is status
