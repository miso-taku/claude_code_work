"""プロジェクト状況取得ユースケース。"""

from project_dashboard.domain.models.project_status import ProjectStatus
from project_dashboard.domain.repositories.project_status_repository import (
    ProjectStatusRepository,
)


class GetProjectStatusUseCase:
    """リポジトリからプロジェクト状況を取得する（手順の調整のみ）。"""

    def __init__(self, repository: ProjectStatusRepository) -> None:
        self._repository = repository

    def execute(self) -> ProjectStatus:
        return self._repository.load()
