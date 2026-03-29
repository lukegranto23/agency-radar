import unittest

from agency_radar.analysis import summarize_awards
from agency_radar.config import Profile
from agency_radar.prospects import rank_prospects, slugify
from agency_radar.sales import PitchContext, render_followup_email, render_outreach_email
from agency_radar.usaspending import Award


def make_profile() -> Profile:
    return Profile(
        slug="federal_it",
        name="Federal IT Services Radar",
        description="desc",
        target_buyer="small federal contractors, subcontractors, capture consultants, and MSPs",
        naics_codes=["541512"],
        award_type_codes=["A"],
        lookback_days=365,
        expiring_within_days=180,
        top_n_awards=5,
        top_n_entities=4,
        keywords=["cloud"],
    )


class ProspectTests(unittest.TestCase):
    def test_rank_prospects_prefers_expiring_recipients(self) -> None:
        profile = make_profile()
        awards = [
            Award("A1", "Signal Corp", 250_000_000.0, "2026-01-01", "2026-05-01", "Agency X", "1"),
            Award("A2", "Signal Corp", 45_000_000.0, "2026-01-20", "2026-06-01", "Agency Y", "2"),
            Award("A3", "Slow Prime", 900_000_000.0, "2026-01-02", "2027-02-01", "Agency Z", "3"),
        ]
        summary = summarize_awards(profile, awards, spending_over_time=[])
        prospects = rank_prospects(profile, summary, limit=5)
        self.assertEqual(prospects[0].company_name, "Signal Corp")
        self.assertGreater(prospects[0].expiring_award_count, prospects[1].expiring_award_count)
        self.assertIn("capture manager", prospects[0].target_role)

    def test_sales_templates_include_rationale_and_sample_report(self) -> None:
        profile = make_profile()
        awards = [
            Award("A1", "Signal Corp", 250_000_000.0, "2026-01-01", "2026-05-01", "Agency X", "1"),
        ]
        summary = summarize_awards(profile, awards, spending_over_time=[])
        context = PitchContext(
            company_name="Signal Corp",
            first_name="Alex",
            sender_name="Luke",
            rationale="2 expiring awards and recent wins",
            sample_report_url="https://example.com/sample",
        )
        initial = render_outreach_email(profile, summary, context)
        followup = render_followup_email(profile, summary, context)
        self.assertIn("Why I thought of Signal Corp", initial)
        self.assertIn("https://example.com/sample", initial)
        self.assertIn("https://example.com/sample", followup)

    def test_slugify_normalizes_company_names(self) -> None:
        self.assertEqual(slugify("ACME Federal, Inc."), "acme-federal-inc")


if __name__ == "__main__":
    unittest.main()
