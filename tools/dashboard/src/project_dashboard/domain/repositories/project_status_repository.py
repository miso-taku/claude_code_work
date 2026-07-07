"""プロジェクト状況リポジトリのインターフェース定義。

実装は infrastructure/repositories/ に置く（依存性逆転）。
"""

from abc import ABC, abstractmethod

from project_dashboard.domain.models.project_status import ProjectStatus


class ProjectStatusRepository(ABC):
    """ProjectStatus集約の読み取り専用リポジトリ。"""

    @abstractmethod
    def load(self) -> ProjectStatus:
        """現在のプロジェクト状況を読み込む。"""
