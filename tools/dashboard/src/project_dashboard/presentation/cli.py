"""ダッシュボード生成CLI。

`uv run dashboard` で実行される（pyproject.toml の [project.scripts] 参照）。
"""

import argparse
import sys
from pathlib import Path

from project_dashboard.application.usecases.get_project_status import GetProjectStatusUseCase
from project_dashboard.infrastructure.repositories.filesystem_project_status_repository import (
    FilesystemProjectStatusRepository,
)
from project_dashboard.presentation.html_renderer import render_dashboard


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dashboard",
        description="プロジェクト状況ダッシュボード（dashboard.html）を生成する",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="リポジトリルート（既定: カレントディレクトリ）",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="出力先HTMLパス（既定: <root>/dashboard.html）",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    root: Path = args.root
    output: Path = args.output if args.output is not None else root / "dashboard.html"

    repository = FilesystemProjectStatusRepository(root=root)
    status = GetProjectStatusUseCase(repository=repository).execute()
    html = render_dashboard(status)

    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(html, encoding="utf-8")
    except OSError as error:
        print(f"エラー: ダッシュボードを書き込めませんでした: {error}", file=sys.stderr)
        return 1

    print(f"ダッシュボードを生成しました: {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
