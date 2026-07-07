"""tasklist.md のテキストからタスク進捗を解析するドメインサービス。

ファイルI/Oは行わず、文字列のみを入力とする純粋関数として実装する。
解析ルールは .steering/20260707-project-dashboard/design.md
「主要なビジネスルール」の項に従う:

- `- [x]` / `- [X]` を完了、`- [ ]` を未完了として数える（ネスト・インデント任意）
- 「## フェーズ」で始まる見出しごとにフェーズ進捗を分割する
- 最初のフェーズ見出しより前のチェックボックス（原則の記述等）は集計しない
- 「## コードレビュー結果」「## 実装後の振り返り」以降は集計しない
"""

import re

from project_dashboard.domain.models.project_status import PhaseProgress, TaskProgress

_CHECKBOX_PATTERN = re.compile(r"^\s*- \[( |x|X)\]")
_PHASE_HEADING_PREFIX = "## フェーズ"
_STOP_HEADINGS = ("## コードレビュー結果", "## 実装後の振り返り")


def parse_tasklist(text: str) -> tuple[TaskProgress, list[PhaseProgress]]:
    """tasklist.md の全体進捗とフェーズ別進捗を解析する。"""
    phases: list[PhaseProgress] = []
    current_phase_name: str | None = None
    current_done = 0
    current_total = 0
    total_done = 0
    total_count = 0

    def close_current_phase() -> None:
        nonlocal current_phase_name
        if current_phase_name is not None:
            phases.append(
                PhaseProgress(
                    name=current_phase_name,
                    progress=TaskProgress(done=current_done, total=current_total),
                )
            )
            current_phase_name = None

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(_STOP_HEADINGS):
            break
        if stripped.startswith(_PHASE_HEADING_PREFIX):
            close_current_phase()
            current_phase_name = stripped.removeprefix("## ").strip()
            current_done = 0
            current_total = 0
            continue
        if current_phase_name is None:
            continue  # 最初のフェーズ見出しより前は集計対象外
        match = _CHECKBOX_PATTERN.match(line)
        if match is None:
            continue
        current_total += 1
        total_count += 1
        if match.group(1) in ("x", "X"):
            current_done += 1
            total_done += 1

    close_current_phase()
    return TaskProgress(done=total_done, total=total_count), phases
