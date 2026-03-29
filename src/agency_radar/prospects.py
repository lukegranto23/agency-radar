from __future__ import annotations

import csv
import html
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from .analysis import RecipientSnapshot, ReportSummary
from .config import Profile


@dataclass(frozen=True)
class Prospect:
    company_name: str
    score: int
    total_award_amount: float
    award_count: int
    expiring_award_count: int
    expiring_award_amount: float
    recent_award_count: int
    top_agencies: list[str]
    target_role: str
    why_now: str
    sample_award_id: str


def slugify(value: str) -> str:
    lowered = value.lower()
    cleaned = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return cleaned or "prospect"


def _sweet_spot_points(total_award_amount: float) -> int:
    if 25_000_000 <= total_award_amount <= 800_000_000:
        return 32
    if 800_000_000 < total_award_amount <= 1_500_000_000:
        return 20
    if 5_000_000 <= total_award_amount < 25_000_000:
        return 12
    if 1_500_000_000 < total_award_amount <= 3_000_000_000:
        return 4
    if total_award_amount > 3_000_000_000:
        return -20
    return 6


def _award_count_points(award_count: int) -> int:
    if award_count >= 12:
        return 18
    if award_count >= 6:
        return 12
    if award_count >= 3:
        return 8
    return 4


def _expiring_amount_points(expiring_award_amount: float) -> int:
    if expiring_award_amount >= 500_000_000:
        return 25
    if expiring_award_amount >= 100_000_000:
        return 18
    if expiring_award_amount >= 25_000_000:
        return 12
    if expiring_award_amount > 0:
        return 8
    return 0


def _score_snapshot(snapshot: RecipientSnapshot) -> int:
    score = 0
    score += snapshot.expiring_award_count * 18
    score += _expiring_amount_points(snapshot.expiring_award_amount)
    score += _award_count_points(snapshot.award_count)
    score += _sweet_spot_points(snapshot.total_award_amount)
    score += min(len(snapshot.top_agencies), 3) * 4
    if snapshot.recent_award_count >= 2:
        score += 10
    if snapshot.expiring_award_count == 0:
        score -= 8
    if snapshot.award_count > 12:
        score -= 8
    return score


def _target_role(profile: Profile) -> str:
    if "capture" in profile.target_buyer.lower():
        return "capture manager or BD lead"
    return "BD lead or federal growth lead"


def _why_now(profile: Profile, snapshot: RecipientSnapshot) -> str:
    agency_text = ", ".join(snapshot.top_agencies[:2]) if snapshot.top_agencies else "multiple agencies"
    parts = [
        f"{snapshot.award_count} tracked awards totaling ${snapshot.total_award_amount:,.0f}",
    ]
    if snapshot.expiring_award_count:
        parts.append(
            f"{snapshot.expiring_award_count} expiring inside {profile.expiring_within_days} days"
        )
    if snapshot.recent_award_count:
        parts.append(f"{snapshot.recent_award_count} recent high-value wins in the latest window")
    parts.append(f"active with {agency_text}")
    return "; ".join(parts)


def rank_prospects(profile: Profile, summary: ReportSummary, limit: int = 20) -> list[Prospect]:
    prospects = []
    for snapshot in summary.recipient_snapshots:
        if snapshot.total_award_amount < 1_000_000:
            continue
        prospects.append(
            Prospect(
                company_name=snapshot.name,
                score=_score_snapshot(snapshot),
                total_award_amount=snapshot.total_award_amount,
                award_count=snapshot.award_count,
                expiring_award_count=snapshot.expiring_award_count,
                expiring_award_amount=snapshot.expiring_award_amount,
                recent_award_count=snapshot.recent_award_count,
                top_agencies=snapshot.top_agencies,
                target_role=_target_role(profile),
                why_now=_why_now(profile, snapshot),
                sample_award_id=snapshot.example_award_id,
            )
        )
    prospects.sort(
        key=lambda item: (
            item.score,
            item.expiring_award_count,
            item.total_award_amount,
            item.award_count,
        ),
        reverse=True,
    )
    return prospects[:limit]


def render_prospects_markdown(profile: Profile, prospects: list[Prospect]) -> str:
    lines = [
        f"# {profile.name} buyer targets",
        "",
        f"Top ranked prospects for selling {profile.name.lower()} as a recurring brief.",
        "",
    ]
    for prospect in prospects:
        agencies = ", ".join(prospect.top_agencies[:3]) or "multiple agencies"
        lines.extend(
            [
                f"## {prospect.company_name}",
                f"- Score: {prospect.score}",
                f"- Why now: {prospect.why_now}",
                f"- Likely owner: {prospect.target_role}",
                f"- Agency mix: {agencies}",
                f"- Example award: {prospect.sample_award_id or 'n/a'}",
                "",
            ]
        )
    return "\n".join(lines)


def render_prospects_html(profile: Profile, prospects: list[Prospect]) -> str:
    cards = []
    for prospect in prospects:
        cards.append(
            "<article class='card'>"
            f"<div class='score'>Score {prospect.score}</div>"
            f"<h2>{html.escape(prospect.company_name)}</h2>"
            f"<p>{html.escape(prospect.why_now)}</p>"
            f"<p><strong>Likely owner:</strong> {html.escape(prospect.target_role)}</p>"
            f"<p><strong>Agencies:</strong> {html.escape(', '.join(prospect.top_agencies[:3]) or 'multiple agencies')}</p>"
            f"<p><strong>Example award:</strong> {html.escape(prospect.sample_award_id or 'n/a')}</p>"
            "</article>"
        )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(profile.name)} Buyer Targets</title>
  <style>
    :root {{
      --bg: #0e1417;
      --panel: #151e24;
      --line: rgba(255,255,255,0.08);
      --text: #eef1ea;
      --muted: #b5beb4;
      --accent: #7ad8b2;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: system-ui, sans-serif; background: linear-gradient(180deg, #10171c, var(--bg)); color: var(--text); }}
    .shell {{ width: min(1100px, calc(100% - 2rem)); margin: 0 auto; padding: 3rem 0; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; }}
    .card {{ background: var(--panel); border: 1px solid var(--line); border-radius: 20px; padding: 1.2rem; }}
    .score {{ color: var(--accent); font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; font-size: 0.8rem; }}
    p {{ color: var(--muted); line-height: 1.6; }}
    @media (max-width: 860px) {{ .grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <main class="shell">
    <p>{html.escape(profile.name)} sales targets</p>
    <h1>Prospects most likely to buy this brief</h1>
    <div class="grid">{''.join(cards) or '<p>No buyer targets yet.</p>'}</div>
  </main>
</body>
</html>
"""


def write_prospects_csv(path: Path, prospects: list[Prospect]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "company_name",
                "score",
                "total_award_amount",
                "award_count",
                "expiring_award_count",
                "expiring_award_amount",
                "recent_award_count",
                "top_agencies",
                "target_role",
                "why_now",
                "sample_award_id",
            ]
        )
        for prospect in prospects:
            writer.writerow(
                [
                    prospect.company_name,
                    prospect.score,
                    prospect.total_award_amount,
                    prospect.award_count,
                    prospect.expiring_award_count,
                    prospect.expiring_award_amount,
                    prospect.recent_award_count,
                    "|".join(prospect.top_agencies),
                    prospect.target_role,
                    prospect.why_now,
                    prospect.sample_award_id,
                ]
            )


def write_prospects_json(path: Path, prospects: list[Prospect]) -> None:
    path.write_text(json.dumps([asdict(item) for item in prospects], indent=2), encoding="utf-8")
