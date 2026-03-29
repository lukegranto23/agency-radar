from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class CheckoutEvent:
    created_at: datetime
    amount_total: int | None
    currency: str
    customer_email: str
    payment_status: str
    status: str
    mode: str
    subscription_id: str
    payment_link: str


def parse_checkout_sessions(payload: dict) -> list[CheckoutEvent]:
    events = []
    for item in payload.get("data", []):
        created_value = item.get("created")
        created_at = datetime.fromtimestamp(created_value, tz=timezone.utc) if created_value else datetime.now(timezone.utc)
        customer_details = item.get("customer_details") or {}
        subscription = item.get("subscription")
        if isinstance(subscription, dict):
            subscription_id = subscription.get("id", "")
        else:
            subscription_id = subscription or ""
        events.append(
            CheckoutEvent(
                created_at=created_at,
                amount_total=item.get("amount_total"),
                currency=(item.get("currency") or "").upper(),
                customer_email=customer_details.get("email", "") or item.get("customer_email", "") or "",
                payment_status=item.get("payment_status", ""),
                status=item.get("status", ""),
                mode=item.get("mode", ""),
                subscription_id=subscription_id,
                payment_link=item.get("payment_link", "") or "",
            )
        )
    return events


def fetch_recent_checkout_sessions(api_key: str, limit: int = 10) -> list[CheckoutEvent]:
    query = urlencode(
        [
            ("limit", str(limit)),
            ("expand[]", "data.customer_details"),
            ("expand[]", "data.subscription"),
        ]
    )
    request = Request(
        f"https://api.stripe.com/v1/checkout/sessions?{query}",
        headers={"Authorization": f"Bearer {api_key}"},
        method="GET",
    )
    with urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return parse_checkout_sessions(payload)
