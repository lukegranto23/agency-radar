from __future__ import annotations

import csv
import html
from pathlib import Path

from .analysis import ReportSummary, ScoredAward
from .config import Profile
from .usaspending import Award


REQUEST_SAMPLE_URL = "https://github.com/lukegranto23/agency-radar/issues/new?template=sample-request.yml"


def money(value: float) -> str:
    return f"${value:,.0f}"


def award_table_rows(awards: list[Award]) -> str:
    rows = []
    for award in awards:
        rows.append(
            "<tr>"
            f"<td>{html.escape(award.award_id)}</td>"
            f"<td>{html.escape(award.recipient_name)}</td>"
            f"<td>{html.escape(award.awarding_agency)}</td>"
            f"<td>{money(award.award_amount)}</td>"
            f"<td>{html.escape(award.start_date)}</td>"
            f"<td>{html.escape(award.end_date)}</td>"
            "</tr>"
        )
    return "\n".join(rows) if rows else "<tr><td colspan='6'>No awards found for this profile.</td></tr>"


def scored_award_rows(items: list[ScoredAward]) -> str:
    rows = []
    for item in items:
        award = item.award
        rows.append(
            "<tr>"
            f"<td>{item.opportunity_score}</td>"
            f"<td>{item.days_to_expiry}</td>"
            f"<td>{html.escape(award.award_id)}</td>"
            f"<td>{html.escape(award.recipient_name)}</td>"
            f"<td>{html.escape(award.awarding_agency)}</td>"
            f"<td>{money(award.award_amount)}</td>"
            f"<td>{html.escape(award.end_date)}</td>"
            "</tr>"
        )
    return "\n".join(rows) if rows else "<tr><td colspan='7'>No expiring awards in the current window.</td></tr>"


def entity_list(items) -> str:
    if not items:
        return "<li>No data</li>"
    return "\n".join(
        f"<li><strong>{html.escape(item.name)}</strong> · {money(item.total_award_amount)} across {item.award_count} awards</li>"
        for item in items
    )


def spending_rows(spending_over_time: list[dict]) -> str:
    if not spending_over_time:
        return "<tr><td colspan='2'>No history</td></tr>"
    return "\n".join(
        "<tr>"
        f"<td>{html.escape(str(item.get('time_period', {}).get('fiscal_year', '')))}</td>"
        f"<td>{money(float(item.get('aggregated_amount', 0.0) or 0.0))}</td>"
        "</tr>"
        for item in spending_over_time
    )


def render_html(profile: Profile, summary: ReportSummary) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(profile.name)} | Agency Radar</title>
  <style>
    :root {{
      --bg: #0f1418;
      --panel: #192127;
      --panel-2: #202a31;
      --text: #eef0ea;
      --muted: #b8c0b5;
      --accent: #77d9b0;
      --line: rgba(255,255,255,0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: radial-gradient(circle at top left, rgba(119,217,176,0.16), transparent 22%), var(--bg);
      color: var(--text);
      line-height: 1.6;
    }}
    .shell {{ width: min(1180px, calc(100% - 2rem)); margin: 0 auto; }}
    .hero {{ padding: 3rem 0 1.5rem; }}
    .hero h1 {{ font-size: clamp(2.4rem, 6vw, 4.6rem); line-height: 0.95; margin: 0 0 1rem; }}
    .hero p {{ color: var(--muted); max-width: 820px; }}
    .stats {{
      display: grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 1rem; margin: 1.75rem 0 0;
    }}
    .card, .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 20px;
      padding: 1.2rem;
    }}
    .card strong {{ display: block; font-size: 2rem; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; padding: 1rem 0 2rem; }}
    h2 {{ margin-top: 0; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.95rem; }}
    th, td {{ border-bottom: 1px solid var(--line); padding: 0.7rem; text-align: left; vertical-align: top; }}
    th {{ color: var(--muted); font-weight: 600; }}
    ul {{ margin: 0; padding-left: 1.1rem; }}
    .muted {{ color: var(--muted); }}
    .cta {{
      display: inline-block;
      padding: 0.9rem 1.15rem;
      border-radius: 999px;
      background: var(--accent);
      color: #102018;
      text-decoration: none;
      font-weight: 700;
    }}
    @media (max-width: 900px) {{
      .stats, .grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <p class="muted">Agency Radar</p>
      <h1>{html.escape(profile.name)}</h1>
      <p>{html.escape(profile.description)}</p>
      <p class="muted">Target buyer: {html.escape(profile.target_buyer)} · NAICS: {", ".join(profile.naics_codes)}</p>
      <div class="stats">
        <div class="card">
          <span class="muted">Tracked awards</span>
          <strong>{summary.award_count}</strong>
        </div>
        <div class="card">
          <span class="muted">Award dollars in window</span>
          <strong>{money(summary.total_award_amount)}</strong>
        </div>
        <div class="card">
          <span class="muted">Expiring soon</span>
          <strong>{len(summary.expiring_awards)}</strong>
        </div>
      </div>
    </section>

    <section class="grid">
      <article class="panel">
        <h2>Top agencies</h2>
        <ul>{entity_list(summary.top_agencies)}</ul>
      </article>
      <article class="panel">
        <h2>Top recipients</h2>
        <ul>{entity_list(summary.top_recipients)}</ul>
      </article>
    </section>

    <section class="grid">
      <article class="panel">
        <h2>Federal spend over time</h2>
        <table>
          <thead><tr><th>Fiscal year</th><th>Amount</th></tr></thead>
          <tbody>{spending_rows(summary.spending_over_time)}</tbody>
        </table>
      </article>
      <article class="panel">
        <h2>Expiring awards</h2>
        <table>
          <thead><tr><th>Award ID</th><th>Recipient</th><th>Agency</th><th>Amount</th><th>Start</th><th>End</th></tr></thead>
          <tbody>{award_table_rows(summary.expiring_awards[:profile.top_n_awards])}</tbody>
        </table>
      </article>
    </section>

    <section class="grid">
      <article class="panel">
        <h2>Newly observed awards</h2>
        <table>
          <thead><tr><th>Award ID</th><th>Recipient</th><th>Agency</th><th>Amount</th><th>Start</th><th>End</th></tr></thead>
          <tbody>{award_table_rows(summary.newly_seen_awards)}</tbody>
        </table>
      </article>
      <article class="panel">
        <h2>Top recompete candidates</h2>
        <table>
          <thead><tr><th>Score</th><th>Days</th><th>Award ID</th><th>Recipient</th><th>Agency</th><th>Amount</th><th>End</th></tr></thead>
          <tbody>{scored_award_rows(summary.top_expiring_opportunities)}</tbody>
        </table>
      </article>
    </section>

    <section class="panel" style="margin-bottom: 2rem;">
      <h2>Recent high-value awards</h2>
      <table>
        <thead><tr><th>Award ID</th><th>Recipient</th><th>Agency</th><th>Amount</th><th>Start</th><th>End</th></tr></thead>
        <tbody>{award_table_rows(summary.recent_awards)}</tbody>
      </table>
    </section>

    <section class="panel" style="margin-bottom: 2rem;">
      <h2>Need this for your niche?</h2>
      <p class="muted">Request a custom brief or recurring version of this report and include the agencies, competitors, or NAICS codes you care about.</p>
      <a class="cta" href="{REQUEST_SAMPLE_URL}">Request a custom brief</a>
    </section>
  </main>
</body>
</html>
"""


def render_markdown(profile: Profile, summary: ReportSummary) -> str:
    lines = [
        f"# {profile.name}",
        "",
        profile.description,
        "",
        f"- Target buyer: {profile.target_buyer}",
        f"- NAICS: {', '.join(profile.naics_codes)}",
        f"- Award window count: {summary.award_count}",
        f"- Award dollars in window: {money(summary.total_award_amount)}",
        f"- Expiring within {profile.expiring_within_days} days: {len(summary.expiring_awards)}",
        f"- Newly observed in latest run: {len(summary.newly_seen_awards)}",
        "",
        "## Top agencies",
    ]
    for item in summary.top_agencies:
        lines.append(f"- {item.name}: {money(item.total_award_amount)} across {item.award_count} awards")
    lines.extend(["", "## Top recipients"])
    for item in summary.top_recipients:
        lines.append(f"- {item.name}: {money(item.total_award_amount)} across {item.award_count} awards")
    lines.extend(["", "## Recent awards"])
    for award in summary.recent_awards:
        lines.append(
            f"- {award.award_id} | {award.recipient_name} | {award.awarding_agency} | {money(award.award_amount)} | {award.end_date}"
        )
    lines.extend(["", "## Top recompete candidates"])
    for item in summary.top_expiring_opportunities:
        lines.append(
            f"- Score {item.opportunity_score} | {item.days_to_expiry} days | {item.award.award_id} | {item.award.recipient_name} | {item.award.awarding_agency} | {money(item.award.award_amount)}"
        )
    return "\n".join(lines) + "\n"


def write_awards_csv(path: Path, awards: list[Award]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["award_id", "recipient_name", "awarding_agency", "award_amount", "start_date", "end_date", "generated_internal_id"])
        for award in awards:
            writer.writerow(
                [
                    award.award_id,
                    award.recipient_name,
                    award.awarding_agency,
                    award.award_amount,
                    award.start_date,
                    award.end_date,
                    award.generated_internal_id,
                ]
            )


def load_awards_csv(path: Path) -> list[Award]:
    if not path.exists():
        return []
    awards: list[Award] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            awards.append(
                Award(
                    award_id=row.get("award_id", ""),
                    recipient_name=row.get("recipient_name", ""),
                    award_amount=float(row.get("award_amount", 0.0) or 0.0),
                    start_date=row.get("start_date", ""),
                    end_date=row.get("end_date", ""),
                    awarding_agency=row.get("awarding_agency", ""),
                    generated_internal_id=row.get("generated_internal_id", ""),
                )
            )
    return awards
