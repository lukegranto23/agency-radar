from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any
from urllib.request import Request, urlopen

from .config import Profile


BASE_URL = "https://api.usaspending.gov/api/v2"


@dataclass(frozen=True)
class Award:
    award_id: str
    recipient_name: str
    award_amount: float
    start_date: str
    end_date: str
    awarding_agency: str
    generated_internal_id: str


def iso_today() -> date:
    return date.today()


def fetch_json(endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    request = Request(
        f"{BASE_URL}{endpoint}",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def build_filters(profile: Profile, start_date: date, end_date: date) -> dict[str, Any]:
    return {
        "time_period": [
            {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            }
        ],
        "naics_codes": profile.naics_codes,
        "award_type_codes": profile.award_type_codes,
    }


def fetch_awards(profile: Profile, start_date: date, end_date: date, limit: int) -> list[Award]:
    awards: list[Award] = []
    seen_keys: set[str] = set()
    page = 1
    remaining = limit

    while remaining > 0:
        page_limit = min(remaining, 100)
        payload = {
            "filters": build_filters(profile, start_date, end_date),
            "fields": [
                "Award ID",
                "Recipient Name",
                "Award Amount",
                "Start Date",
                "End Date",
                "Awarding Agency",
            ],
            "sort": "Award Amount",
            "order": "desc",
            "page": page,
            "limit": page_limit,
        }
        response = fetch_json("/search/spending_by_award/", payload)
        results = response.get("results", [])
        if not results:
            break
        for result in results:
            generated_internal_id = result.get("generated_internal_id", "")
            dedupe_key = "|".join(
                [
                    str(result.get("Award ID", "")),
                    str(result.get("Recipient Name", "")),
                    str(result.get("Awarding Agency", "")),
                    str(result.get("Start Date", "")),
                    str(result.get("End Date", "")),
                ]
            )
            if dedupe_key in seen_keys:
                continue
            seen_keys.add(dedupe_key)
            awards.append(
                Award(
                    award_id=result.get("Award ID", ""),
                    recipient_name=result.get("Recipient Name", ""),
                    award_amount=float(result.get("Award Amount", 0.0) or 0.0),
                    start_date=result.get("Start Date", ""),
                    end_date=result.get("End Date", ""),
                    awarding_agency=result.get("Awarding Agency", ""),
                    generated_internal_id=generated_internal_id,
                )
            )
        remaining -= len(results)
        if len(results) < page_limit:
            break
        page += 1
    return awards


def fetch_spending_over_time(profile: Profile, start_date: date, end_date: date) -> list[dict[str, Any]]:
    payload = {
        "filters": build_filters(profile, start_date, end_date),
        "group": "fiscal_year",
        "subawards": False,
    }
    response = fetch_json("/search/spending_over_time/", payload)
    return response.get("results", [])


def default_window(profile: Profile) -> tuple[date, date]:
    end = iso_today()
    start = end - timedelta(days=profile.lookback_days)
    return start, end
