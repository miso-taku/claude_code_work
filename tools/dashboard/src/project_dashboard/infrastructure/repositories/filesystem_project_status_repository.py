"""ファイルシステムと git からプロジェクト状況を構築するリポジトリ実装。

git コマンドの出力解析は純粋関数として分離し、ユニットテスト可能にする。
git 実行関数（run_git）は注入可能とし、テストではフェイクに差し替える。
"""

import subprocess
from collections.abc import Callable
from pathlib import Path

from project_dashboard.domain.models.project_status import (
    Commit,
    DocumentStatus,
    ProjectStatus,
    SourceStats,
    SteeringWork,
    TaskProgress,
)
from project_dashboard.domain.repositories.project_status_repository import (
    ProjectStatusRepository,
)
from project_dashboard.domain.services.tasklist_parser import parse_tasklist

_LOG_SEPARATOR = "|"

GitRunner = Callable[[list[str]], str]

FORMAL_DOCUMENTS: tuple[tuple[str, str], ...] = (
    ("product-requirements.md", "プロダクト要求定義書（PRD）"),
    ("functional-design.md", "機能設計書"),
    ("architecture.md", "技術仕様書"),
    ("repository-structure.md", "リポジトリ構造定義書"),
    ("development-guidelines.md", "開発ガイドライン"),
    ("glossary.md", "用語集"),
)


def parse_git_log(text: str) -> list[Commit]:
    """`git log --format=%h|%ad|%s` の出力をコミットのリストに変換する。

    サブジェクトに区切り文字が含まれてもよいよう、分割は先頭2箇所のみ行う。
    形式に合わない行は無視する。
    """
    commits: list[Commit] = []
    for line in text.splitlines():
        parts = line.split(_LOG_SEPARATOR, maxsplit=2)
        if len(parts) != 3 or not parts[0].strip():
            continue
        commits.append(Commit(hash=parts[0].strip(), date=parts[1].strip(), subject=parts[2]))
    return commits


def parse_git_status_is_clean(text: str) -> bool:
    """`git status --porcelain` の出力から作業ツリーがクリーンかを判定する。"""
    return text.strip() == ""


class FilesystemProjectStatusRepository(ProjectStatusRepository):
    """リポジトリルート配下の走査と git コマンドで ProjectStatus を構築する。"""

    def __init__(self, root: Path, run_git: GitRunner | None = None) -> None:
        self._root = root
        self._run_git = run_git if run_git is not None else self._run_git_subprocess

    def load(self) -> ProjectStatus:
        branch, commits, is_clean = self._load_git_info()
        return ProjectStatus(
            project_name=self._root.name,
            branch=branch,
            is_clean=is_clean,
            commits=commits,
            documents=self._load_documents(),
            steerings=self._load_steerings(),
            source_stats=self._count_python_stats(self._root / "src"),
            tests_stats=self._count_python_stats(self._root / "tests"),
        )

    def _run_git_subprocess(self, args: list[str]) -> str:
        """git を実行して標準出力を返す（shell=False・引数リスト形式のみ）。"""
        result = subprocess.run(
            ["git", *args],
            cwd=self._root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
        return result.stdout

    def _load_git_info(self) -> tuple[str, list[Commit], bool]:
        """git 情報を取得する。git が使えない環境でも生成を継続できるよう防御する。"""
        try:
            log_text = self._run_git(["log", "--format=%h|%ad|%s", "--date=format:%Y-%m-%d"])
            status_text = self._run_git(["status", "--porcelain"])
            branch = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"]).strip()
        except (OSError, subprocess.SubprocessError):
            return "unknown", [], True
        return branch or "unknown", parse_git_log(log_text), parse_git_status_is_clean(status_text)

    def _load_documents(self) -> list[DocumentStatus]:
        docs_dir = self._root / "docs"
        return [
            DocumentStatus(name=name, description=description, exists=(docs_dir / name).is_file())
            for name, description in FORMAL_DOCUMENTS
        ]

    def _load_steerings(self) -> list[SteeringWork]:
        steering_dir = self._root / ".steering"
        if not steering_dir.is_dir():
            return []
        works: list[SteeringWork] = []
        for work_dir in sorted(steering_dir.iterdir(), key=lambda p: p.name, reverse=True):
            if not work_dir.is_dir():
                continue
            tasklist_path = work_dir / "tasklist.md"
            if tasklist_path.is_file():
                text = tasklist_path.read_text(encoding="utf-8", errors="replace")
                progress, phases = parse_tasklist(text)
            else:
                progress, phases = TaskProgress(done=0, total=0), []
            works.append(SteeringWork(name=work_dir.name, progress=progress, phases=phases))
        return works

    def _count_python_stats(self, target_dir: Path) -> SourceStats:
        if not target_dir.is_dir():
            return SourceStats(file_count=0, line_count=0)
        file_count = 0
        line_count = 0
        for path in target_dir.rglob("*.py"):
            file_count += 1
            text = path.read_text(encoding="utf-8", errors="replace")
            line_count += len(text.splitlines())
        return SourceStats(file_count=file_count, line_count=line_count)
