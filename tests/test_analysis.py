import unittest

from agency_radar.analysis import summarize_awards
from agency_radar.config import Profile
from agency_radar.usaspending import Award


def make_profile() -> Profile:
    return Profile(
        slug="test",
        name="Test Profile",
        description="desc",
        target_buyer="buyer",
        naics_codes=["541512"],
        award_type_codes=["A"],
        lookback_days=365,
        expiring_within_days=180,
        top_n_awards=5,
        top_n_entities=3,
        keywords=["cyber"],
    )


class AnalysisTests(unittest.TestCase):
    def test_summarize_awards_groups_totals(self) -> None:
        profile = make_profile()
        awards = [
            Award("A1", "Recipient A", 100.0, "2026-01-01", "2026-05-01", "Agency X", "1"),
            Award("A2", "Recipient A", 50.0, "2026-01-05", "2026-10-01", "Agency X", "2"),
            Award("A3", "Recipient B", 75.0, "2026-03-01", "2026-04-15", "Agency Y", "3"),
        ]
        summary = summarize_awards(profile, awards, spending_over_time=[])
        self.assertEqual(summary.award_count, 3)
        self.assertEqual(summary.total_award_amount, 225.0)
        self.assertEqual(summary.top_recipients[0].name, "Recipient A")
        self.assertEqual(summary.top_recipients[0].total_award_amount, 150.0)
        self.assertEqual(summary.top_agencies[0].name, "Agency X")
        self.assertEqual(summary.top_agencies[0].award_count, 2)

    def test_summarize_awards_flags_new_and_scores_expiring(self) -> None:
        profile = make_profile()
        previous = [
            Award("A0", "Recipient Z", 10.0, "2025-01-01", "2026-01-01", "Agency Z", "0"),
        ]
        awards = [
            Award("A1", "Recipient A", 600_000_000.0, "2026-01-01", "2026-05-01", "Agency X", "1"),
            Award("A2", "Recipient B", 20_000_000.0, "2026-01-05", "2026-10-01", "Agency Y", "2"),
        ]
        summary = summarize_awards(profile, awards, spending_over_time=[], previous_awards=previous)
        self.assertEqual(len(summary.newly_seen_awards), 2)
        self.assertGreaterEqual(summary.top_expiring_opportunities[0].opportunity_score, 50)
        self.assertEqual(summary.top_expiring_opportunities[0].award.award_id, "A1")
        self.assertEqual(summary.recipient_snapshots[0].name, "Recipient A")
        self.assertEqual(summary.recipient_snapshots[0].expiring_award_count, 1)
        self.assertIn("Agency X", summary.recipient_snapshots[0].top_agencies)


if __name__ == "__main__":
    unittest.main()
