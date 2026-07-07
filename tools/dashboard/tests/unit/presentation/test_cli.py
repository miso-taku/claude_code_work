"""CLI（presentation/cli.py）のユニットテスト。"""

from pathlib import Path

from project_dashboard.presentation.cli import main


class TestMain:
    """git リポジトリでないディレクトリでも生成が継続する仕様（design.md）を前提に、
    tmp_path をそのままリポジトリルートとして使う。"""

    def test_ダッシュボードがデフォルトパスに生成される(self, tmp_path: Path) -> None:
        exit_code = main(["--root", str(tmp_path)])

        output = tmp_path / "dashboard.html"
        assert exit_code == 0
        assert output.is_file()
        assert "<!doctype html>" in output.read_text(encoding="utf-8").lower()

    def test_outputオプションで出力先を変更できる(self, tmp_path: Path) -> None:
        custom = tmp_path / "out" / "status.html"

        exit_code = main(["--root", str(tmp_path), "--output", str(custom)])

        assert exit_code == 0
        assert custom.is_file()

    def test_書き込みできない出力先の場合は終了コード1を返す(self, tmp_path: Path) -> None:
        # 出力先パスにディレクトリを置いて書き込み失敗させる
        blocked = tmp_path / "dashboard.html"
        blocked.mkdir()

        exit_code = main(["--root", str(tmp_path), "--output", str(blocked)])

        assert exit_code == 1
