from __future__ import annotations

from dataclasses import dataclass

from .analysis import ReportSummary
from .config import Profile


@dataclass(frozen=True)
class PitchContext:
    company_name: str
    first_name: str
    sender_name: str
    rationale: str = ""
    sample_report_url: str = "sample-report.html"
    checkout_url: str = ""
    contact_url: str = "mailto:lukegranto04@gmail.com?subject=Agency%20Radar%20custom%20brief"


def render_outreach_email(profile: Profile, summary: ReportSummary, context: PitchContext) -> str:
    offer_name = profile.name.replace(" Radar", "")
    top_agency = summary.top_agencies[0].name if summary.top_agencies else "federal buyers"
    top_recompete = summary.top_expiring_opportunities[0].award if summary.top_expiring_opportunities else None
    lines = [
        f"Subject: A narrow {offer_name.lower()} brief for {context.company_name}",
        "",
        f"{context.first_name},",
        "",
        f"I built a narrow procurement-intelligence brief for firms chasing {offer_name.lower()} work.",
        "",
    ]
    if context.rationale:
        lines.extend(
            [
                f"Why I thought of {context.company_name}:",
                f"- {context.rationale}",
                "",
            ]
        )
    lines.extend(
        [
        "It tracks:",
        f"- the agencies spending most heavily in your slice of the market, currently led by {top_agency}",
        f"- expiring contracts that may turn into recompetes, with {len(summary.expiring_awards)} expiring within {profile.expiring_within_days} days",
        f"- the incumbents winning the most dollars, which helps with teaming and competitive positioning",
        "",
        ]
    )
    if top_recompete:
        lines.extend(
            [
                "One current example from the latest run:",
                f"- {top_recompete.award_id} | {top_recompete.recipient_name} | {top_recompete.awarding_agency} | ends {top_recompete.end_date}",
                "",
            ]
        )
    lines.extend(
        [
            f"If useful, I can send you the sample report and turn it into a recurring weekly brief or custom watchlist for your niche: {context.sample_report_url}",
            "",
        ]
    )
    if context.checkout_url:
        lines.extend(
            [
                f"If you already know the fit is there, the starter checkout is here: {context.checkout_url}",
                "",
            ]
        )
    lines.extend(
        [
            f"Direct reply path: {context.contact_url}",
            "",
            f"- {context.sender_name}",
        ]
    )
    return "\n".join(lines) + "\n"


def render_followup_email(profile: Profile, summary: ReportSummary, context: PitchContext) -> str:
    offer_name = profile.name.replace(" Radar", "")
    top_agency = summary.top_agencies[0].name if summary.top_agencies else "federal buyers"
    lines = [
        f"Subject: Re: {offer_name} brief for {context.company_name}",
        "",
        f"{context.first_name},",
        "",
        f"Following up on the {offer_name.lower()} brief I mentioned.",
        "",
        f"It currently shows {len(summary.expiring_awards)} awards expiring within {profile.expiring_within_days} days and {top_agency} as the heaviest spending agency in this slice.",
        "",
        f"If you want, I can send the sample report or set up a custom watchlist here: {context.sample_report_url}",
    ]
    if context.checkout_url:
        lines.extend(
            [
                f"If you want to start immediately, the starter checkout is here: {context.checkout_url}",
                "",
            ]
        )
    lines.extend(
        [
            f"Direct reply path: {context.contact_url}",
            "",
            f"- {context.sender_name}",
        ]
    )
    return "\n".join(lines) + "\n"
