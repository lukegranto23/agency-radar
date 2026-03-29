from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "profiles.json"


@dataclass(frozen=True)
class Profile:
    slug: str
    name: str
    description: str
    target_buyer: str
    naics_codes: list[str]
    award_type_codes: list[str]
    lookback_days: int
    expiring_within_days: int
    top_n_awards: int
    top_n_entities: int
    keywords: list[str]


def load_profiles(config_path: Path | None = None) -> dict[str, Profile]:
    config_path = config_path or DEFAULT_CONFIG_PATH
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    return {
        slug: Profile(slug=slug, **payload)
        for slug, payload in raw["profiles"].items()
    }


def load_profile(slug: str, config_path: Path | None = None) -> Profile:
    profiles = load_profiles(config_path)
    try:
        return profiles[slug]
    except KeyError as exc:
        raise SystemExit(f"Unknown profile: {slug}. Available: {', '.join(sorted(profiles))}") from exc


def to_jsonable_profile(profile: Profile) -> dict[str, Any]:
    return {
        "slug": profile.slug,
        "name": profile.name,
        "description": profile.description,
        "target_buyer": profile.target_buyer,
        "naics_codes": profile.naics_codes,
        "award_type_codes": profile.award_type_codes,
        "lookback_days": profile.lookback_days,
        "expiring_within_days": profile.expiring_within_days,
        "top_n_awards": profile.top_n_awards,
        "top_n_entities": profile.top_n_entities,
        "keywords": profile.keywords,
    }

