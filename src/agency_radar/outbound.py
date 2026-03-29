from __future__ import annotations

import csv
import json
import smtplib
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class Contact:
    company_name: str
    segment: str
    why_this_company: str
    contact_surface: str
    general_email: str
    phone: str
    named_contact: str
    named_role: str


@dataclass(frozen=True)
class DraftEmail:
    company_name: str
    email: str
    subject: str
    body: str
    segment: str


@dataclass(frozen=True)
class SendResult:
    company_name: str
    email: str
    segment: str
    mode: str
    status: str
    detail: str


def load_contacts(path: Path) -> list[Contact]:
    contacts = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            contacts.append(
                Contact(
                    company_name=row["company_name"],
                    segment=row["segment"],
                    why_this_company=row["why_this_company"],
                    contact_surface=row["contact_surface"],
                    general_email=row["general_email"],
                    phone=row["phone"],
                    named_contact=row["named_contact"],
                    named_role=row["named_role"],
                )
            )
    return contacts


def split_subject_body(content: str) -> tuple[str, str]:
    lines = content.strip().splitlines()
    if not lines:
        return "", ""
    first = lines[0]
    subject = first.removeprefix("Subject: ").strip() if first.lower().startswith("subject:") else first.strip()
    body = "\n".join(lines[1:]).strip()
    return subject, body


def first_name(value: str) -> str:
    if not value:
        return "there"
    return value.split()[0]


def filter_contacts(contacts: Iterable[Contact], segment: str | None = None, limit: int | None = None) -> list[Contact]:
    filtered = [contact for contact in contacts if contact.general_email]
    if segment:
        filtered = [contact for contact in filtered if contact.segment == segment]
    return filtered[:limit] if limit else filtered


def load_sent_keys(path: Path) -> set[tuple[str, str]]:
    if not path.exists():
        return set()
    sent = set()
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row.get("status") == "sent":
                sent.add((row.get("company_name", ""), row.get("email", "")))
    return sent


def append_send_log(path: Path, results: list[SendResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = path.exists()
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        if not file_exists:
            writer.writerow(["sent_at", "mode", "company_name", "email", "segment", "status", "detail"])
        sent_at = datetime.now(timezone.utc).isoformat()
        for result in results:
            writer.writerow([sent_at, result.mode, result.company_name, result.email, result.segment, result.status, result.detail])


def send_via_smtp(
    draft: DraftEmail,
    from_email: str,
    smtp_host: str,
    smtp_port: int,
    smtp_username: str,
    smtp_password: str,
    reply_to: str | None = None,
) -> SendResult:
    message = EmailMessage()
    message["From"] = from_email
    message["To"] = draft.email
    message["Subject"] = draft.subject
    if reply_to:
        message["Reply-To"] = reply_to
    message.set_content(draft.body)
    with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30) as server:
        server.login(smtp_username, smtp_password)
        server.send_message(message)
    return SendResult(draft.company_name, draft.email, draft.segment, "smtp", "sent", "queued via smtp")


def send_via_resend(
    draft: DraftEmail,
    api_key: str,
    from_email: str,
    reply_to: str | None = None,
) -> SendResult:
    payload = {
        "from": from_email,
        "to": [draft.email],
        "subject": draft.subject,
        "text": draft.body,
    }
    if reply_to:
        payload["reply_to"] = reply_to
    request = Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
        return SendResult(draft.company_name, draft.email, draft.segment, "resend", "sent", data.get("id", "sent"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8")
        return SendResult(draft.company_name, draft.email, draft.segment, "resend", "failed", detail[:300])

