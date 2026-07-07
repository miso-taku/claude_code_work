"""tasklist.md 解析ドメインサービスのユニットテスト。"""

from project_dashboard.domain.models.project_status import TaskProgress
from project_dashboard.domain.services.tasklist_parser import parse_tasklist


class TestParseTasklist:
    def test_完了と未完了のチェックボックスを集計できる(self) -> None:
        text = "\n".join(
            [
                "# タスクリスト",
                "",
                "## フェーズ1: 実装",
                "",
                "- [x] タスクA",
                "- [ ] タスクB",
                "- [x] タスクC",
            ]
        )

        progress, phases = parse_tasklist(text)

        assert progress == TaskProgress(done=2, total=3)
        assert len(phases) == 1
        assert phases[0].name == "フェーズ1: 実装"
        assert phases[0].progress == TaskProgress(done=2, total=3)

    def test_ネストしたサブタスクも集計される(self) -> None:
        text = "\n".join(
            [
                "## フェーズ1: 実装",
                "- [x] 親タスク",
                "  - [x] RED: テスト作成",
                "  - [ ] GREEN: 実装",
            ]
        )

        progress, _ = parse_tasklist(text)

        assert progress == TaskProgress(done=2, total=3)

    def test_大文字Xのチェックも完了として数える(self) -> None:
        text = "\n".join(["## フェーズ1: 実装", "- [X] タスクA"])

        progress, _ = parse_tasklist(text)

        assert progress == TaskProgress(done=1, total=1)

    def test_複数フェーズがフェーズ別に分割される(self) -> None:
        text = "\n".join(
            [
                "## フェーズ1: 設計",
                "- [x] タスクA",
                "## フェーズ2: 実装",
                "- [ ] タスクB",
                "- [ ] タスクC",
            ]
        )

        progress, phases = parse_tasklist(text)

        assert progress == TaskProgress(done=1, total=3)
        assert [phase.name for phase in phases] == ["フェーズ1: 設計", "フェーズ2: 実装"]
        assert phases[1].progress == TaskProgress(done=0, total=2)

    def test_フェーズ見出しより前のチェックボックスは集計対象外(self) -> None:
        text = "\n".join(
            [
                "# タスクリスト",
                "## 🚨 タスク完全完了の原則",
                "- [ ] 全てのタスクを`[x]`にすること",  # 原則の記述であり集計しない
                "## フェーズ1: 実装",
                "- [x] タスクA",
            ]
        )

        progress, phases = parse_tasklist(text)

        assert progress == TaskProgress(done=1, total=1)
        assert len(phases) == 1

    def test_コードレビュー結果セクション以降は集計対象外(self) -> None:
        text = "\n".join(
            [
                "## フェーズ1: 実装",
                "- [x] タスクA",
                "## コードレビュー結果",
                "- [ ] レビュー例のチェックボックス",
                "## 実装後の振り返り",
                "- [ ] 振り返り例のチェックボックス",
            ]
        )

        progress, phases = parse_tasklist(text)

        assert progress == TaskProgress(done=1, total=1)
        assert [phase.name for phase in phases] == ["フェーズ1: 実装"]

    def test_境界値_空文字列は進捗ゼロでフェーズなし(self) -> None:
        progress, phases = parse_tasklist("")

        assert progress == TaskProgress(done=0, total=0)
        assert phases == []

    def test_チェックボックスのないフェーズは進捗ゼロとして扱われる(self) -> None:
        text = "\n".join(["## フェーズ1: 準備", "説明文のみ"])

        progress, phases = parse_tasklist(text)

        assert progress == TaskProgress(done=0, total=0)
        assert phases[0].progress == TaskProgress(done=0, total=0)
