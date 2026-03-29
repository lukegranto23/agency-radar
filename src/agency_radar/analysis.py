from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from .config import Profile
from .usaspending import Award


@dataclass(frozen=True)
class RankedEntity:
    name: str
    total_award_amount: float
    award_count: int


@dataclass(frozen=True)
class ScoredAward:
    award: Award
    days_to_expiry: int
    opportunity_score: int


@dataclass(frozen=True)
class RecipientSnapshot:
    name: str
    total_award_amount: float
    award_count: int
    expiring_award_count: int
    expiring_award_amount: float
    recent_award_count: int
    top_agencies: list[str]
    example_award_id: str


@dataclass(frozen=True)
class ReportSummary:
    total_award_amount: float
    award_count: int
    recent_awards: list[Award]
    expiring_awards: list[Award]
    top_expiring_opportunities: list[ScoredAward]
    newly_seen_awards: list[Award]
    top_agencies: list[RankedEntity]
    top_recipients: list[RankedEntity]
    recipient_snapshots: list[RecipientSnapshot]
    spending_over_time: list[dict]


def _parse_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _dedupe_key(award: Award) -> str:
    return "|".join(
        [
            award.award_id,
            award.recipient_name,
            award.awarding_agency,
            award.start_date,
            award.end_date,
        ]
    )


def _score_expiring_award(award: Award, days_to_expiry: int) -> int:
    amount = award.award_amount
    if amount >= 500_000_000:
        amount_points = 50
    elif amount >= 100_000_000:
        amount_points = 40
    elif amount >= 50_000_000:
        amount_points = 30
    elif amount >= 10_000_000:
        amount_points = 20
    else:
        amount_points = 10

    if days_to_expiry <= 30:
        timing_points = 40
    elif days_to_expiry <= 60:
        timing_points = 30
    elif days_to_expiry <= 90:
        timing_points = 20
    elif days_to_expiry <= 180:
        timing_points = 10
    else:
        timing_points = 0

    return amount_points + timing_points


def summarize_awards(
    profile: Profile,
    awards: list[Award],
    spending_over_time: list[dict],
    previous_awards: list[Award] | None = None,
) -> ReportSummary:
    total_award_amount = sum(award.award_amount for award in awards)
    agency_totals: dict[str, float] = defaultdict(float)
    agency_counts: Counter[str] = Counter()
    recipient_totals: dict[str, float] = defaultdict(float)
    recipient_counts: Counter[str] = Counter()
    recipient_awards: dict[str, list[Award]] = defaultdict(list)

    for award in awards:
        agency_totals[award.awarding_agency] += award.award_amount
        agency_counts[award.awarding_agency] += 1
        recipient_totals[award.recipient_name] += award.award_amount
        recipient_counts[award.recipient_name] += 1
        recipient_awards[award.recipient_name].append(award)

    top_agencies = sorted(
        (
            RankedEntity(name=name, total_award_amount=amount, award_count=agency_counts[name])
            for name, amount in agency_totals.items()
        ),
        key=lambda item: item.total_award_amount,
        reverse=True,
    )[: profile.top_n_entities]

    top_recipients = sorted(
        (
            RankedEntity(name=name, total_award_amount=amount, award_count=recipient_counts[name])
            for name, amount in recipient_totals.items()
        ),
        key=lambda item: item.total_award_amount,
        reverse=True,
    )[: profile.top_n_entities]

    today = date.today()
    expiring_cutoff = today + timedelta(days=profile.expiring_within_days)
    expiring_awards = [
        award
        for award in awards
        if (end := _parse_date(award.end_date)) is not None and today <= end <= expiring_cutoff
    ]
    expiring_awards.sort(key=lambda award: award.end_date)

    scored_expiring = []
    for award in expiring_awards:
        end_date = _parse_date(award.end_date)
        if not end_date:
            continue
        days_to_expiry = (end_date - today).days
        scored_expiring.append(
            ScoredAward(
                award=award,
                days_to_expiry=days_to_expiry,
                opportunity_score=_score_expiring_award(award, days_to_expiry),
            )
        )
    scored_expiring.sort(
        key=lambda item: (item.opportunity_score, item.award.award_amount),
        reverse=True,
    )

    recent_awards = sorted(awards, key=lambda award: award.start_date, reverse=True)[: profile.top_n_awards]
    previous_keys = {_dedupe_key(award) for award in (previous_awards or [])}
    newly_seen_awards = [
        award for award in recent_awards if _dedupe_key(award) not in previous_keys
    ][: profile.top_n_awards]
    recent_award_ids = {_dedupe_key(award) for award in recent_awards}

    recipient_snapshots = []
    for recipient_name, recipient_award_list in recipient_awards.items():
        expiring_for_recipient = [award for award in expiring_awards if award.recipient_name == recipient_name]
        agency_mix = Counter(award.awarding_agency for award in recipient_award_list)
        top_agencies_for_recipient = [name for name, _count in agency_mix.most_common(3)]
        recipient_snapshots.append(
            RecipientSnapshot(
                name=recipient_name,
                total_award_amount=recipient_totals[recipient_name],
                award_count=recipient_counts[recipient_name],
                expiring_award_count=len(expiring_for_recipient),
                expiring_award_amount=sum(award.award_amount for award in expiring_for_recipient),
                recent_award_count=sum(1 for award in recipient_award_list if _dedupe_key(award) in recent_award_ids),
                top_agencies=top_agencies_for_recipient,
                example_award_id=recipient_award_list[0].award_id if recipient_award_list else "",
            )
        )
    recipient_snapshots.sort(
        key=lambda item: (item.expiring_award_count, item.total_award_amount, item.award_count),
        reverse=True,
    )

    return ReportSummary(
        total_award_amount=total_award_amount,
        award_count=len(awards),
        recent_awards=recent_awards,
        expiring_awards=expiring_awards,
        top_expiring_opportunities=scored_expiring[: profile.top_n_awards],
        newly_seen_awards=newly_seen_awards,
        top_agencies=top_agencies,
        top_recipients=top_recipients,
        recipient_snapshots=recipient_snapshots[: max(profile.top_n_entities * 3, 12)],
        spending_over_time=spending_over_time,
    )
