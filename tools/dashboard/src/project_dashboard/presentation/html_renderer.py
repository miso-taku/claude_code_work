"""ProjectStatus をレトロポップデザインの自己完結HTMLに変換するレンダラー。

- 外部CDN・外部フォント・外部画像を参照しない（オフラインで開ける）
- 動的値はすべて html.escape() を通す（リポジトリ由来の任意文字列対策）
- データ表現色は色覚多様性・コントラスト検証済みの4色
  （#E03A24 / #008E6E / #C77800 / #2D55C4）を使う
"""

import html
from datetime import date

from project_dashboard.domain.models.project_status import (
    ProjectStatus,
    RoadmapStage,
    SteeringWork,
)

_MAX_COMMITS = 10

_CSS = """
  :root{
    --paper:#FFF4E4; --panel:#FFFBF2; --ink:#221C15; --ink-soft:#6B5F4E;
    --pop-red:#FF5D47; --pop-yellow:#FFC833; --pop-mint:#35C4AE; --pop-pink:#FF7BAC;
    --mark-red:#E03A24; --mark-green:#008E6E; --mark-amber:#C77800; --mark-blue:#2D55C4;
    --line:3px solid var(--ink); --shadow:6px 6px 0 var(--ink); --shadow-sm:4px 4px 0 var(--ink);
    --r:14px;
    --sans:'Helvetica Neue',Arial,'Hiragino Kaku Gothic ProN','Yu Gothic UI',Meiryo,sans-serif;
    --mono:Consolas,'Courier New',monospace;
  }
  *{box-sizing:border-box;margin:0;padding:0;}
  html,body{background:var(--paper);color:var(--ink);font-family:var(--sans);}
  body{
    background-image:radial-gradient(rgba(34,28,21,.09) 1.2px, transparent 1.3px);
    background-size:18px 18px; line-height:1.55;
  }
  .wrap{max-width:1060px;margin:0 auto;padding:36px 20px 64px;}
  .masthead{
    background:var(--panel);border:var(--line);border-radius:var(--r);
    box-shadow:var(--shadow);padding:26px 28px 22px;position:relative;overflow:hidden;
  }
  .masthead::before{
    content:"";position:absolute;inset:0 0 auto 0;height:12px;
    background:repeating-linear-gradient(90deg,
      var(--pop-red) 0 28px,var(--pop-yellow) 28px 56px,
      var(--pop-mint) 56px 84px,var(--pop-pink) 84px 112px);
    border-bottom:var(--line);
  }
  .eyebrow{
    font-family:var(--mono);font-size:12px;letter-spacing:.22em;
    text-transform:uppercase;color:var(--ink-soft);margin:14px 0 6px;
  }
  h1{font-size:clamp(26px,4.5vw,40px);font-weight:900;line-height:1.15;text-wrap:balance;}
  h1 .bang{color:var(--mark-red);}
  .sub{margin-top:8px;color:var(--ink-soft);font-size:15px;}
  .badges{display:flex;flex-wrap:wrap;gap:10px;margin-top:16px;}
  .badge{
    display:inline-flex;align-items:center;gap:7px;border:2.5px solid var(--ink);
    border-radius:999px;background:#fff;box-shadow:3px 3px 0 var(--ink);
    padding:5px 14px;font-size:13px;font-weight:700;
  }
  .badge .dot{width:9px;height:9px;border-radius:50%;border:2px solid var(--ink);flex:none;}
  .badge.yellow{background:var(--pop-yellow);}
  .badge.mint{background:var(--pop-mint);}
  .badge.pink{background:var(--pop-pink);}
  .sticker{
    position:absolute;top:30px;right:26px;background:var(--pop-yellow);
    border:var(--line);border-radius:999px;box-shadow:var(--shadow-sm);
    padding:12px 18px;font-weight:900;font-size:14px;letter-spacing:.05em;
    transform:rotate(6deg);text-align:center;line-height:1.25;
  }
  .sticker small{
    display:block;font-family:var(--mono);font-weight:400;font-size:10px;letter-spacing:.15em;
  }
  @media (max-width:720px){
    .sticker{position:static;display:inline-block;margin-top:14px;transform:rotate(-2deg);}
  }
  .tiles{
    display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));
    gap:18px;margin-top:26px;
  }
  .tile{
    background:var(--panel);border:var(--line);border-radius:var(--r);
    box-shadow:var(--shadow-sm);padding:16px 18px 14px;position:relative;
  }
  .tile .k{
    font-family:var(--mono);font-size:11px;letter-spacing:.18em;
    text-transform:uppercase;color:var(--ink-soft);
  }
  .tile .v{
    font-size:38px;font-weight:900;line-height:1.1;margin-top:2px;
    font-variant-numeric:tabular-nums;
  }
  .tile .v .of{font-size:20px;color:var(--ink-soft);font-weight:700;}
  .tile .note{font-size:12.5px;color:var(--ink-soft);margin-top:4px;}
  .tile::after{
    content:"";position:absolute;top:-9px;right:14px;width:22px;height:22px;
    border:2.5px solid var(--ink);border-radius:50%;
  }
  .tile.t-green::after{background:var(--pop-mint);}
  .tile.t-yellow::after{background:var(--pop-yellow);}
  .tile.t-red::after{background:var(--pop-red);}
  .tile.t-pink::after{background:var(--pop-pink);}
  .v.ok{color:var(--mark-green);}
  .v.zero{color:var(--mark-red);}
  .grid{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin-top:26px;}
  @media (max-width:860px){.grid{grid-template-columns:1fr;}}
  .card{
    background:var(--panel);border:var(--line);border-radius:var(--r);
    box-shadow:var(--shadow);padding:20px 22px;
  }
  .card.full{grid-column:1/-1;}
  .card h2{font-size:18px;font-weight:900;margin-bottom:4px;display:flex;align-items:center;gap:10px;}
  .card h2 .tag{
    font-family:var(--mono);font-size:10px;font-weight:400;letter-spacing:.18em;
    text-transform:uppercase;border:2px solid var(--ink);border-radius:6px;
    padding:2px 8px;background:var(--pop-yellow);
  }
  .card .lead{font-size:13px;color:var(--ink-soft);margin-bottom:14px;}
  .chip{
    display:inline-flex;align-items:center;gap:6px;font-size:12px;font-weight:800;
    letter-spacing:.04em;border:2.5px solid var(--ink);border-radius:999px;
    padding:3px 11px;flex:none;
  }
  .chip.done{background:var(--pop-mint);}
  .chip.todo{background:#fff;color:var(--ink-soft);border-style:dashed;}
  .chip.now{background:var(--pop-yellow);}
  .steps{list-style:none;display:flex;flex-direction:column;}
  .step{display:flex;gap:16px;position:relative;padding-bottom:22px;}
  .step:last-child{padding-bottom:0;}
  .step::before{
    content:"";position:absolute;left:17px;top:38px;bottom:0;width:3px;
    background:repeating-linear-gradient(180deg,var(--ink) 0 6px,transparent 6px 12px);
  }
  .step:last-child::before{display:none;}
  .step .num{
    width:38px;height:38px;flex:none;border:var(--line);border-radius:50%;
    display:grid;place-items:center;font-weight:900;font-size:16px;
    background:#fff;position:relative;z-index:1;
  }
  .step.done .num{background:var(--pop-mint);}
  .step.now .num{background:var(--pop-yellow);box-shadow:var(--shadow-sm);}
  .step .body{padding-top:4px;min-width:0;}
  .step .t{font-weight:900;font-size:15.5px;display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
  .step .d{font-size:13px;color:var(--ink-soft);margin-top:3px;}
  code{
    font-family:var(--mono);font-size:.92em;background:#F3E7CF;
    border:1.5px solid rgba(34,28,21,.35);border-radius:5px;padding:1px 5px;
  }
  .bar{
    height:22px;border:2.5px solid var(--ink);border-radius:999px;
    background:#fff;overflow:hidden;
  }
  .bar .fill{
    height:100%;border-right:2.5px solid var(--ink);
    background:repeating-linear-gradient(45deg,var(--mark-green) 0 10px,#00A883 10px 20px);
  }
  .bar .fill.empty{width:0;border-right:none;}
  .bar-row{display:flex;align-items:center;gap:12px;margin-top:10px;}
  .bar-row .bar{flex:1;}
  .bar-row .pct{
    font-family:var(--mono);font-weight:700;font-size:14px;width:84px;text-align:right;
    font-variant-numeric:tabular-nums;flex:none;
  }
  .docs{list-style:none;display:flex;flex-direction:column;gap:9px;}
  .docs li{
    display:flex;align-items:center;gap:11px;border:2.5px solid var(--ink);
    border-radius:10px;background:#fff;padding:9px 13px;
  }
  .docs .box{
    width:20px;height:20px;flex:none;border:2.5px solid var(--ink);border-radius:5px;
    background:#fff;display:grid;place-items:center;font-weight:900;font-size:13px;
  }
  .docs .box.checked{background:var(--pop-mint);}
  .docs .name{font-family:var(--mono);font-size:13px;font-weight:700;min-width:0;overflow-wrap:anywhere;}
  .docs .what{font-size:12px;color:var(--ink-soft);margin-left:auto;text-align:right;flex:none;}
  @media (max-width:480px){.docs .what{display:none;}}
  .steering-work{border:2.5px solid var(--ink);border-radius:10px;background:#fff;padding:13px 15px;}
  .steering-work + .steering-work{margin-top:12px;}
  .steering-work .head{display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
  .steering-work .name{font-family:var(--mono);font-size:13px;font-weight:700;overflow-wrap:anywhere;}
  .phasegrid{
    display:grid;grid-template-columns:auto 1fr auto;gap:6px 12px;
    align-items:center;margin-top:12px;font-size:12.5px;
  }
  .phasegrid .pn{font-weight:800;}
  .phasegrid .pc{
    font-family:var(--mono);font-variant-numeric:tabular-nums;
    color:var(--ink-soft);text-align:right;white-space:nowrap;
  }
  .minibar{height:14px;border:2px solid var(--ink);border-radius:999px;background:#fff;overflow:hidden;}
  .minibar i{display:block;height:100%;background:var(--mark-green);}
  .commits{list-style:none;display:flex;flex-direction:column;gap:9px;}
  .commits li{display:flex;align-items:center;gap:12px;font-size:13.5px;flex-wrap:wrap;}
  .commits .hash{
    font-family:var(--mono);font-size:12px;font-weight:700;background:var(--ink);
    color:var(--paper);border-radius:6px;padding:2px 8px;flex:none;
  }
  .commits .date{
    font-family:var(--mono);font-size:12px;color:var(--ink-soft);flex:none;
    font-variant-numeric:tabular-nums;
  }
  .commits .msg{font-weight:700;overflow-wrap:anywhere;}
  .card.next{background:var(--ink);color:var(--paper);box-shadow:6px 6px 0 var(--pop-red);}
  .card.next h2{color:var(--paper);}
  .card.next .lead{color:#CDBFA8;}
  .card.next .t{font-weight:900;font-size:14.5px;}
  .card.next .d{font-size:12.5px;color:#CDBFA8;margin-top:2px;}
  .card.next code{background:#3A3126;border-color:#6B5F4E;color:var(--pop-yellow);}
  .empty-note{font-size:13px;color:var(--ink-soft);}
  footer{
    margin-top:30px;text-align:center;font-family:var(--mono);font-size:11px;
    letter-spacing:.2em;text-transform:uppercase;color:var(--ink-soft);
  }
"""


def _e(value: str) -> str:
    """HTMLエスケープの短縮エイリアス。"""
    return html.escape(value)


def _render_masthead(status: ProjectStatus, generated_on: str) -> str:
    clean_label = "作業ツリー CLEAN" if status.is_clean else "未コミットの変更あり"
    clean_color = "var(--pop-mint)" if status.is_clean else "var(--pop-red)"
    if status.current_stage is RoadmapStage.DOCUMENTATION:
        sticker_main, sticker_sub = "ドキュメント作成中", "WRITE THE DOCS"
    else:
        sticker_main, sticker_sub = "実装フェーズ", "BUILD IT"
    return f"""
  <header class="masthead">
    <p class="eyebrow">Project Status Dashboard ・ {_e(generated_on)} 生成</p>
    <h1>{_e(status.project_name)}<span class="bang">!</span></h1>
    <p class="sub">スペック駆動開発テンプレート — DDD × TDD</p>
    <div class="badges">
      <span class="badge yellow">Python + uv</span>
      <span class="badge"><span class="dot" style="background:var(--pop-mint)"></span>branch: {_e(status.branch)}</span>
      <span class="badge"><span class="dot" style="background:{clean_color}"></span>{clean_label}</span>
      <span class="badge pink">DDD × TDD 必須</span>
    </div>
    <div class="sticker">{sticker_main}<small>{sticker_sub}</small></div>
  </header>"""


def _render_tiles(status: ProjectStatus) -> str:
    docs = status.documents_progress
    docs_class = "ok" if docs.total > 0 and docs.done == docs.total else "zero"
    src_class = "ok" if status.source_stats.line_count > 0 else "zero"
    return f"""
  <section class="tiles" aria-label="サマリー">
    <div class="tile t-green">
      <div class="k">Steering 完了</div>
      <div class="v ok">{status.completed_steering_count}<span class="of"> / {len(status.steerings)}</span></div>
      <div class="note">.steering/ の作業単位</div>
    </div>
    <div class="tile t-red">
      <div class="k">正式ドキュメント</div>
      <div class="v {docs_class}">{docs.done}<span class="of"> / {docs.total}</span></div>
      <div class="note">docs/ の北極星ドキュメント</div>
    </div>
    <div class="tile t-yellow">
      <div class="k">実装コード</div>
      <div class="v {src_class}">{status.source_stats.line_count:,}<span class="of"> 行</span></div>
      <div class="note">src/ {status.source_stats.file_count}ファイル ・ tests/ {status.tests_stats.file_count}ファイル</div>
    </div>
    <div class="tile t-pink">
      <div class="k">コミット</div>
      <div class="v">{len(status.commits)}</div>
      <div class="note">{_e(status.commits[0].subject) if status.commits else "コミットなし"}</div>
    </div>
  </section>"""


def _render_roadmap(status: ProjectStatus) -> str:
    documenting = status.current_stage is RoadmapStage.DOCUMENTATION
    step2_class, step2_chip = (
        ("now", '<span class="chip now">★ いまここ</span>')
        if documenting
        else ("done", '<span class="chip done">✔ 完了</span>')
    )
    step3_class, step3_chip = (
        ("", '<span class="chip todo">未着手</span>')
        if documenting
        else ("now", '<span class="chip now">★ いまここ</span>')
    )
    return f"""
    <section class="card">
      <h2>ロードマップ <span class="tag">Roadmap</span></h2>
      <p class="lead">スペック駆動開発の3ステップ。</p>
      <ol class="steps">
        <li class="step done">
          <div class="num">1</div>
          <div class="body">
            <div class="t">テンプレート整備 <span class="chip done">✔ 完了</span></div>
            <div class="d">DDD/TDDガイド・スキル・コマンド・エージェントの整備</div>
          </div>
        </li>
        <li class="step {step2_class}">
          <div class="num">2</div>
          <div class="body">
            <div class="t">ドキュメント作成 {step2_chip}</div>
            <div class="d"><code>/setup-project</code> で6つの永続ドキュメントを作成</div>
          </div>
        </li>
        <li class="step {step3_class}">
          <div class="num">3</div>
          <div class="body">
            <div class="t">機能実装 {step3_chip}</div>
            <div class="d"><code>/add-feature</code> で Red → Green → Refactor のTDD実装</div>
          </div>
        </li>
      </ol>
    </section>"""


def _render_documents(status: ProjectStatus) -> str:
    items = []
    for doc in status.documents:
        box = '<span class="box checked">✔</span>' if doc.exists else '<span class="box"></span>'
        items.append(
            f'        <li>{box}<span class="name">{_e(doc.name)}</span>'
            f'<span class="what">{_e(doc.description)}</span></li>'
        )
    body = (
        "\n".join(items)
        if items
        else '        <li><span class="empty-note">ドキュメント定義がありません</span></li>'
    )
    progress = status.documents_progress
    return f"""
    <section class="card">
      <h2>永続ドキュメント <span class="tag">docs/</span></h2>
      <p class="lead">プロジェクトの「北極星」。整備状況 {progress.done} / {progress.total}。</p>
      <ul class="docs">
{body}
      </ul>
    </section>"""


def _render_steering_work(work: SteeringWork) -> str:
    chip = (
        '<span class="chip done">✔ 完了</span>'
        if work.is_completed
        else '<span class="chip now">進行中</span>'
    )
    phase_rows = "".join(
        f"""
          <span class="pn">{_e(phase.name)}</span>
          <span class="minibar"><i style="width:{phase.progress.percent}%"></i></span>
          <span class="pc">{phase.progress.done}/{phase.progress.total}</span>"""
        for phase in work.phases
    )
    phase_grid = f'<div class="phasegrid">{phase_rows}\n        </div>' if work.phases else ""
    fill = (
        f'<div class="fill" style="width:{work.progress.percent}%"></div>'
        if work.progress.percent > 0
        else '<div class="fill empty"></div>'
    )
    return f"""
      <div class="steering-work">
        <div class="head"><span class="name">{_e(work.name)}</span>{chip}</div>
        <div class="bar-row">
          <div class="bar" role="img" aria-label="タスク完了率 {work.progress.percent}%">{fill}</div>
          <div class="pct">{work.progress.done}/{work.progress.total}</div>
        </div>
        {phase_grid}
      </div>"""


def _render_steerings(status: ProjectStatus) -> str:
    body = (
        "".join(_render_steering_work(work) for work in status.steerings)
        if status.steerings
        else '<p class="empty-note">ステアリング作業はまだありません。</p>'
    )
    return f"""
    <section class="card full">
      <h2>作業実績 <span class="tag">.steering/</span></h2>
      <p class="lead">作業単位ごとの tasklist.md 進捗（新しい順）。</p>
      {body}
    </section>"""


def _render_commits(status: ProjectStatus) -> str:
    items = "\n".join(
        f'        <li><span class="hash">{_e(commit.hash)}</span>'
        f'<span class="date">{_e(commit.date)}</span>'
        f'<span class="msg">{_e(commit.subject)}</span></li>'
        for commit in status.commits[:_MAX_COMMITS]
    )
    if not items:
        items = (
            '        <li><span class="empty-note">コミット履歴を取得できませんでした。</span></li>'
        )
    return f"""
    <section class="card">
      <h2>コミット履歴 <span class="tag">git log</span></h2>
      <p class="lead">全{len(status.commits)}コミット（最新{min(len(status.commits), _MAX_COMMITS)}件を表示）。</p>
      <ul class="commits">
{items}
      </ul>
    </section>"""


def _render_next_action(status: ProjectStatus) -> str:
    if status.current_stage is RoadmapStage.DOCUMENTATION:
        title = "<code>/setup-project</code> でドキュメントを作成する"
        detail = (
            "docs/ideas/ にアイデアを書き、6つの永続ドキュメントを対話的に作成（1ファイルずつ承認）"
        )
    else:
        title = "<code>/add-feature</code> で機能を実装する"
        detail = "ステアリングファイルを作成し、テストを先に書く（Red → Green → Refactor）"
    return f"""
    <section class="card next">
      <h2>ネクストアクション <span class="tag">Next Up</span></h2>
      <p class="lead">現在のロードマップ段階から自動判定。</p>
      <div class="t">{title}</div>
      <div class="d">{detail}</div>
    </section>"""


def render_dashboard(status: ProjectStatus, generated_on: str | None = None) -> str:
    """プロジェクト状況をダッシュボードHTML文字列に変換する。"""
    if generated_on is None:
        generated_on = date.today().isoformat()
    return f"""<!doctype html>
<html lang="ja" data-stage="{status.current_stage.value}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_e(status.project_name)} ステータス</title>
<style>{_CSS}</style>
</head>
<body>
<div class="wrap">
{_render_masthead(status, generated_on)}
{_render_tiles(status)}
  <div class="grid">
{_render_roadmap(status)}
{_render_documents(status)}
{_render_steerings(status)}
{_render_commits(status)}
{_render_next_action(status)}
  </div>
  <footer>{_e(status.project_name)} ・ spec-driven development ・ generated {_e(generated_on)}</footer>
</div>
</body>
</html>
"""
