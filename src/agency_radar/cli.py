from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from .analysis import ReportSummary, summarize_awards
from .config import DEFAULT_CONFIG_PATH, Profile, load_profile, load_profiles, to_jsonable_profile
from .outbound import DraftEmail, append_send_log, filter_contacts, load_contacts, load_sent_keys, send_via_resend, send_via_smtp, split_subject_body
from .prospects import rank_prospects, render_prospects_html, render_prospects_markdown, slugify, write_prospects_csv, write_prospects_json
from .render import load_awards_csv, render_html, render_markdown, write_awards_csv
from .sales import PitchContext, render_followup_email, render_outreach_email
from .site import make_published_report, render_catalog_html, write_catalog_json
from .usaspending import default_window, fetch_awards, fetch_spending_over_time


ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = ROOT / "reports"
DOCS_DIR = ROOT / "docs"
DOCS_REPORTS_DIR = DOCS_DIR / "reports"
DOCS_DATA_DIR = DOCS_DIR / "data"
DEFAULT_CONTACTS_PATH = ROOT / "data" / "initial_outreach_contacts.csv"
DEFAULT_OUTREACH_LOG = ROOT / "data" / "outreach_log.csv"


@dataclass(frozen=True)
class BuildArtifact:
    profile: Profile
    summary: ReportSummary
    paths: dict[str, str]


def _fetch_profile_snapshot(profile: Profile) -> tuple[list, ReportSummary]:
    start_date, end_date = default_window(profile)
    awards = fetch_awards(profile, start_date, end_date, limit=250)
    spending_over_time = fetch_spending_over_time(
        profile,
        start_date.replace(year=max(start_date.year - 2, 2008)),
        end_date,
    )
    previous_awards = load_awards_csv(REPORTS_DIR / f"{profile.slug}.csv")
    summary = summarize_awards(profile, awards, spending_over_time, previous_awards=previous_awards)
    return awards, summary


def build_report(
    profile_slug: str,
    output_stem: str | None = None,
    publish_sample: bool = True,
) -> BuildArtifact:
    profile = load_profile(profile_slug)
    awards, summary = _fetch_profile_snapshot(profile)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    stem = output_stem or profile.slug
    html_path = REPORTS_DIR / f"{stem}.html"
    md_path = REPORTS_DIR / f"{stem}.md"
    csv_path = REPORTS_DIR / f"{stem}.csv"
    json_path = REPORTS_DIR / f"{stem}.json"
    sample_report_path = DOCS_DIR / "sample-report.html"

    html_path.write_text(render_html(profile, summary), encoding="utf-8")
    md_path.write_text(render_markdown(profile, summary), encoding="utf-8")
    write_awards_csv(csv_path, awards)
    json_path.write_text(
        json.dumps(
            {
                "profile": to_jsonable_profile(profile),
                "summary": {
                    "award_count": summary.award_count,
                    "total_award_amount": summary.total_award_amount,
                    "expiring_awards": len(summary.expiring_awards),
                    "newly_seen_awards": len(summary.newly_seen_awards),
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    if publish_sample:
        sample_report_path.write_text(html_path.read_text(encoding="utf-8"), encoding="utf-8")
    return BuildArtifact(
        profile=profile,
        summary=summary,
        paths={
            "html": str(html_path),
            "markdown": str(md_path),
            "csv": str(csv_path),
            "json": str(json_path),
            "sample_html": str(sample_report_path),
        },
    )


def build_all_reports() -> dict[str, BuildArtifact]:
    outputs: dict[str, BuildArtifact] = {}
    for slug in sorted(load_profiles(DEFAULT_CONFIG_PATH)):
        outputs[slug] = build_report(slug, slug, publish_sample=slug == "federal_it")
    return outputs


def build_prospect_assets(profile_slug: str, top: int = 20) -> dict[str, str]:
    profile = load_profile(profile_slug)
    _awards, summary = _fetch_profile_snapshot(profile)
    prospects = rank_prospects(profile, summary, limit=top)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    md_path = REPORTS_DIR / f"{profile.slug}_prospects.md"
    csv_path = REPORTS_DIR / f"{profile.slug}_prospects.csv"
    json_path = REPORTS_DIR / f"{profile.slug}_prospects.json"
    html_path = REPORTS_DIR / f"{profile.slug}_prospects.html"
    md_path.write_text(render_prospects_markdown(profile, prospects), encoding="utf-8")
    write_prospects_csv(csv_path, prospects)
    write_prospects_json(json_path, prospects)
    html_path.write_text(render_prospects_html(profile, prospects), encoding="utf-8")
    return {
        "markdown": str(md_path),
        "csv": str(csv_path),
        "json": str(json_path),
        "html": str(html_path),
    }


def build_pitch_batch(
    profile_slug: str,
    top: int = 8,
    sender_name: str = "Luke",
    sample_report_url: str = "sample-report.html",
) -> dict[str, str]:
    profile = load_profile(profile_slug)
    _awards, summary = _fetch_profile_snapshot(profile)
    prospects = rank_prospects(profile, summary, limit=top)
    output_dir = REPORTS_DIR / "pitches" / profile.slug
    output_dir.mkdir(parents=True, exist_ok=True)

    for index, prospect in enumerate(prospects, start=1):
        context = PitchContext(
            company_name=prospect.company_name,
            first_name="there",
            sender_name=sender_name,
            rationale=prospect.why_now,
            sample_report_url=sample_report_url,
        )
        filename_stem = f"{index:02d}-{slugify(prospect.company_name)}"
        content = "\n".join(
            [
                f"# {prospect.company_name}",
                "",
                "## Initial email",
                "",
                render_outreach_email(profile, summary, context).strip(),
                "",
                "## Follow-up email",
                "",
                render_followup_email(profile, summary, context).strip(),
                "",
            ]
        )
        (output_dir / f"{filename_stem}.md").write_text(content, encoding="utf-8")
    return {
        "directory": str(output_dir),
        "count": str(len(prospects)),
    }


def build_site_catalog() -> dict[str, str]:
    artifacts = build_all_reports()
    DOCS_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DATA_DIR.mkdir(parents=True, exist_ok=True)
    published = []
    for slug, artifact in artifacts.items():
        published_report_path = DOCS_REPORTS_DIR / f"{slug}.html"
        published_report_path.write_text(Path(artifact.paths["html"]).read_text(encoding="utf-8"), encoding="utf-8")
        published.append(
            make_published_report(
                artifact.profile,
                artifact.summary,
                f"reports/{slug}.html",
            )
        )
    published.sort(key=lambda item: item.total_award_amount, reverse=True)
    catalog_path = DOCS_DIR / "catalog.html"
    catalog_path.write_text(render_catalog_html(published), encoding="utf-8")
    data_path = DOCS_DATA_DIR / "catalog.json"
    write_catalog_json(data_path, published)
    return {
        "catalog_html": str(catalog_path),
        "catalog_json": str(data_path),
        "reports_dir": str(DOCS_REPORTS_DIR),
    }


def _build_drafts_from_contacts(
    contacts_path: Path,
    sender_name: str,
    segment: str | None = None,
    limit: int | None = None,
    sample_report_base_url: str = "https://lukegranto23.github.io/agency-radar/reports",
) -> list[DraftEmail]:
    contacts = filter_contacts(load_contacts(contacts_path), segment=segment, limit=limit)
    drafts = []
    for contact in contacts:
        profile = load_profile(contact.segment)
        _awards, summary = _fetch_profile_snapshot(profile)
        content = render_outreach_email(
            profile,
            summary,
            PitchContext(
                company_name=contact.company_name,
                first_name=contact.named_contact.split()[0] if contact.named_contact else "there",
                sender_name=sender_name,
                rationale=contact.why_this_company,
                sample_report_url=f"{sample_report_base_url}/{profile.slug}.html",
            ),
        )
        subject, body = split_subject_body(content)
        drafts.append(
            DraftEmail(
                company_name=contact.company_name,
                email=contact.general_email,
                subject=subject,
                body=body,
                segment=contact.segment,
            )
        )
    return drafts


def send_outreach_smtp(
    contacts_path: Path,
    sender_name: str,
    from_email: str,
    smtp_host: str,
    smtp_port: int,
    smtp_username: str,
    smtp_password: str,
    reply_to: str | None = None,
    segment: str | None = None,
    limit: int | None = None,
) -> list[dict[str, str]]:
    sent_keys = load_sent_keys(DEFAULT_OUTREACH_LOG)
    drafts = _build_drafts_from_contacts(contacts_path, sender_name, segment=segment, limit=limit)
    results = []
    for draft in drafts:
        if (draft.company_name, draft.email) in sent_keys:
            results.append({"company_name": draft.company_name, "email": draft.email, "status": "skipped", "detail": "already sent"})
            continue
        outcome = send_via_smtp(
            draft,
            from_email=from_email,
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_username=smtp_username,
            smtp_password=smtp_password,
            reply_to=reply_to,
        )
        append_send_log(DEFAULT_OUTREACH_LOG, [outcome])
        results.append({"company_name": outcome.company_name, "email": outcome.email, "status": outcome.status, "detail": outcome.detail})
    return results


def send_outreach_resend(
    contacts_path: Path,
    sender_name: str,
    from_email: str,
    api_key: str,
    reply_to: str | None = None,
    segment: str | None = None,
    limit: int | None = None,
) -> list[dict[str, str]]:
    sent_keys = load_sent_keys(DEFAULT_OUTREACH_LOG)
    drafts = _build_drafts_from_contacts(contacts_path, sender_name, segment=segment, limit=limit)
    results = []
    batch_results = []
    for draft in drafts:
        if (draft.company_name, draft.email) in sent_keys:
            results.append({"company_name": draft.company_name, "email": draft.email, "status": "skipped", "detail": "already sent"})
            continue
        outcome = send_via_resend(
            draft,
            api_key=api_key,
            from_email=from_email,
            reply_to=reply_to,
        )
        batch_results.append(outcome)
        results.append({"company_name": outcome.company_name, "email": outcome.email, "status": outcome.status, "detail": outcome.detail})
    if batch_results:
        append_send_log(DEFAULT_OUTREACH_LOG, batch_results)
    return results


def list_profiles() -> int:
    profiles = load_profiles(DEFAULT_CONFIG_PATH)
    for slug, profile in sorted(profiles.items()):
        print(f"{slug}: {profile.name}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Agency Radar report builder")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-profiles", help="List configured market profiles")

    build_parser = subparsers.add_parser("build", help="Build report files for a configured profile")
    build_parser.add_argument("--profile", required=True, help="Profile slug from config/profiles.json")
    build_parser.add_argument("--stem", help="Optional output filename stem")

    subparsers.add_parser("build-all", help="Build report files for every configured profile")
    subparsers.add_parser("build-site", help="Build every report and publish the docs catalog")

    prospects_parser = subparsers.add_parser("prospects", help="Generate ranked buyer targets for a configured profile")
    prospects_parser.add_argument("--profile", required=True, help="Profile slug from config/profiles.json")
    prospects_parser.add_argument("--top", type=int, default=20, help="Number of ranked prospects to export")

    pitch_parser = subparsers.add_parser("pitch", help="Generate a personalized outreach email from the latest report data")
    pitch_parser.add_argument("--profile", required=True, help="Profile slug from config/profiles.json")
    pitch_parser.add_argument("--company", required=True, help="Prospect company name")
    pitch_parser.add_argument("--first-name", default="there", help="Recipient first name")
    pitch_parser.add_argument("--sender-name", default="Luke", help="Sender signature name")
    pitch_parser.add_argument("--output", help="Optional file path for the generated email")

    pitch_batch_parser = subparsers.add_parser("pitch-batch", help="Generate outreach sequences for the top ranked prospects in a profile")
    pitch_batch_parser.add_argument("--profile", required=True, help="Profile slug from config/profiles.json")
    pitch_batch_parser.add_argument("--top", type=int, default=8, help="Number of ranked prospects to generate")
    pitch_batch_parser.add_argument("--sender-name", default="Luke", help="Sender signature name")
    pitch_batch_parser.add_argument("--sample-report-url", default="sample-report.html", help="URL to the public sample report")

    smtp_parser = subparsers.add_parser("send-smtp", help="Send outbound emails from the contact list using SMTP")
    smtp_parser.add_argument("--contacts", default=str(DEFAULT_CONTACTS_PATH), help="CSV file of contacts")
    smtp_parser.add_argument("--sender-name", default="Luke", help="Sender signature name")
    smtp_parser.add_argument("--from-email", required=True, help="Visible from email")
    smtp_parser.add_argument("--smtp-host", required=True, help="SMTP host")
    smtp_parser.add_argument("--smtp-port", type=int, default=465, help="SMTP SSL port")
    smtp_parser.add_argument("--smtp-username", required=True, help="SMTP username")
    smtp_parser.add_argument("--smtp-password", required=True, help="SMTP password")
    smtp_parser.add_argument("--reply-to", help="Optional reply-to email")
    smtp_parser.add_argument("--segment", help="Optional segment slug filter")
    smtp_parser.add_argument("--limit", type=int, help="Optional send limit")

    resend_parser = subparsers.add_parser("send-resend", help="Send outbound emails from the contact list using Resend")
    resend_parser.add_argument("--contacts", default=str(DEFAULT_CONTACTS_PATH), help="CSV file of contacts")
    resend_parser.add_argument("--sender-name", default="Luke", help="Sender signature name")
    resend_parser.add_argument("--from-email", required=True, help="Verified sending address")
    resend_parser.add_argument("--api-key", required=True, help="Resend API key")
    resend_parser.add_argument("--reply-to", help="Optional reply-to email")
    resend_parser.add_argument("--segment", help="Optional segment slug filter")
    resend_parser.add_argument("--limit", type=int, help="Optional send limit")

    args = parser.parse_args()
    if args.command == "list-profiles":
        return list_profiles()
    if args.command == "build":
        outputs = build_report(args.profile, args.stem)
        for label, path in outputs.paths.items():
            print(f"{label}: {path}")
        return 0
    if args.command == "build-all":
        outputs = build_all_reports()
        for profile_slug, artifact in outputs.items():
            print(f"[{profile_slug}]")
            for label, path in artifact.paths.items():
                print(f"{label}: {path}")
        return 0
    if args.command == "build-site":
        outputs = build_site_catalog()
        for label, path in outputs.items():
            print(f"{label}: {path}")
        return 0
    if args.command == "prospects":
        outputs = build_prospect_assets(args.profile, top=args.top)
        for label, path in outputs.items():
            print(f"{label}: {path}")
        return 0
    if args.command == "pitch":
        profile = load_profile(args.profile)
        _awards, summary = _fetch_profile_snapshot(profile)
        content = render_outreach_email(
            profile,
            summary,
            PitchContext(
                company_name=args.company,
                first_name=args.first_name,
                sender_name=args.sender_name,
            ),
        )
        if args.output:
            output_path = Path(args.output)
            output_path.write_text(content, encoding="utf-8")
            print(output_path)
        else:
            print(content)
        return 0
    if args.command == "pitch-batch":
        outputs = build_pitch_batch(
            args.profile,
            top=args.top,
            sender_name=args.sender_name,
            sample_report_url=args.sample_report_url,
        )
        for label, path in outputs.items():
            print(f"{label}: {path}")
        return 0
    if args.command == "send-smtp":
        results = send_outreach_smtp(
            Path(args.contacts),
            sender_name=args.sender_name,
            from_email=args.from_email,
            smtp_host=args.smtp_host,
            smtp_port=args.smtp_port,
            smtp_username=args.smtp_username,
            smtp_password=args.smtp_password,
            reply_to=args.reply_to,
            segment=args.segment,
            limit=args.limit,
        )
        for item in results:
            print(f"{item['status']}: {item['company_name']} <{item['email']}> | {item['detail']}")
        return 0
    if args.command == "send-resend":
        results = send_outreach_resend(
            Path(args.contacts),
            sender_name=args.sender_name,
            from_email=args.from_email,
            api_key=args.api_key,
            reply_to=args.reply_to,
            segment=args.segment,
            limit=args.limit,
        )
        for item in results:
            print(f"{item['status']}: {item['company_name']} <{item['email']}> | {item['detail']}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
