"""git コマンド出力を解析する純粋関数のユニットテスト。"""

from project_dashboard.infrastructure.repositories.filesystem_project_status_repository import (
    parse_git_log,
    parse_git_status_is_clean,
)


class TestParseGitLog:
    def test_複数コミットを解析できる(self) -> None:
        text = "\n".join(
            [
                "61dc097|2026-07-06|DDD, TDD対応",
                "7751c90|2026-03-20|最初のコミット",
            ]
        )

        commits = parse_git_log(text)

        assert len(commits) == 2
        assert commits[0].hash == "61dc097"
        assert commits[0].date == "2026-07-06"
        assert commits[0].subject == "DDD, TDD対応"

    def test_サブジェクトに区切り文字を含むコミットを解析できる(self) -> None:
        commits = parse_git_log("abc1234|2026-07-07|feat: a|b|c を追加")

        assert commits[0].subject == "feat: a|b|c を追加"

    def test_境界値_空文字列は空リストになる(self) -> None:
        assert parse_git_log("") == []

    def test_不正な形式の行は無視される(self) -> None:
        text = "\n".join(["61dc097|2026-07-06|正常な行", "壊れた行"])

        commits = parse_git_log(text)

        assert len(commits) == 1


class TestParseGitStatusIsClean:
    def test_出力が空ならクリーンと判定される(self) -> None:
        assert parse_git_status_is_clean("") is True
        assert parse_git_status_is_clean("  \n") is True

    def test_変更があればクリーンでないと判定される(self) -> None:
        assert parse_git_status_is_clean(" M src/main.py\n?? new.txt\n") is False
