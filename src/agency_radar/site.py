from __future__ import annotations

import html
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .analysis import ReportSummary
from .config import Profile

CONTACT_URL = "mailto:lukegranto04@gmail.com?subject=Agency%20Radar%20custom%20brief"
PAYMENT_LINK = "https://buy.stripe.com/4gM5kFdl0069gpg20Ve7m00"


@dataclass(frozen=True)
class PublishedReport:
    slug: str
    profile_name: str
    description: str
    target_buyer: str
    award_count: int
    total_award_amount: float
    expiring_awards: int
    report_href: str


def money(value: float) -> str:
    return f"${value:,.0f}"


def make_published_report(profile: Profile, summary: ReportSummary, report_href: str) -> PublishedReport:
    return PublishedReport(
        slug=profile.slug,
        profile_name=profile.name,
        description=profile.description,
        target_buyer=profile.target_buyer,
        award_count=summary.award_count,
        total_award_amount=summary.total_award_amount,
        expiring_awards=len(summary.expiring_awards),
        report_href=report_href,
    )


def render_catalog_html(entries: list[PublishedReport]) -> str:
    cards = []
    for entry in entries:
        cards.append(
            "<article class='card'>"
            f"<div class='eyebrow'>{html.escape(entry.slug.replace('_', ' '))}</div>"
            f"<h2>{html.escape(entry.profile_name)}</h2>"
            f"<p>{html.escape(entry.description)}</p>"
            f"<p><strong>Target buyer:</strong> {html.escape(entry.target_buyer)}</p>"
            "<div class='stats'>"
            f"<div><span class='label'>Awards</span><strong>{entry.award_count}</strong></div>"
            f"<div><span class='label'>Spend</span><strong>{money(entry.total_award_amount)}</strong></div>"
            f"<div><span class='label'>Expiring</span><strong>{entry.expiring_awards}</strong></div>"
            "</div>"
            f"<a class='cta' href='{html.escape(entry.report_href)}'>Open report</a>"
            "</article>"
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Agency Radar Catalog</title>
  <style>
    :root {{
      --bg: #0d1216;
      --panel: #151d22;
      --line: rgba(255,255,255,0.08);
      --text: #edf1ea;
      --muted: #b6beb5;
      --accent: #7ad7b3;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: system-ui, sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at top left, rgba(122,215,179,0.18), transparent 22%),
        linear-gradient(180deg, #10171c, var(--bg));
    }}
    .shell {{ width: min(1180px, calc(100% - 2rem)); margin: 0 auto; padding: 3rem 0; }}
    .hero {{ padding-bottom: 1.5rem; }}
    .hero h1 {{ font-size: clamp(2.4rem, 6vw, 4.6rem); line-height: 0.95; margin: 0 0 1rem; }}
    .hero p, .card p {{ color: var(--muted); line-height: 1.7; }}
    .eyebrow {{ color: var(--accent); text-transform: uppercase; letter-spacing: 0.08em; font-size: 0.82rem; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; }}
    .card {{ background: var(--panel); border: 1px solid var(--line); border-radius: 22px; padding: 1.2rem; }}
    .stats {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0.8rem; margin: 1rem 0; }}
    .stats div {{ background: rgba(255,255,255,0.02); border: 1px solid var(--line); border-radius: 16px; padding: 0.9rem; }}
    .stats strong {{ display: block; margin-top: 0.35rem; }}
    .label {{ color: var(--muted); font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.06em; }}
    .cta {{ display: inline-block; padding: 0.85rem 1.05rem; border-radius: 999px; background: var(--accent); color: #102018; font-weight: 700; text-decoration: none; }}
    .cta.secondary {{ background: transparent; color: var(--text); border: 1px solid var(--line); }}
    @media (max-width: 900px) {{
      .grid, .stats {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <div class="eyebrow">Agency Radar catalog</div>
      <h1>Sellable procurement briefs across multiple federal niches.</h1>
      <p>Each report is generated from live USAspending data and packaged as a recurring brief rather than a dashboard subscription. This page is meant to make the product legible to buyers fast.</p>
      <p><a class="cta" href="{PAYMENT_LINK}">Start Starter plan</a> <a class="cta secondary" href="{CONTACT_URL}">Email for a custom brief</a></p>
    </section>
    <section class="grid">
      {''.join(cards)}
    </section>
  </main>
</body>
</html>
"""


def write_catalog_json(path: Path, entries: list[PublishedReport]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([asdict(item) for item in entries], indent=2), encoding="utf-8")
