import unittest

from agency_radar.billing import parse_checkout_sessions


class BillingTests(unittest.TestCase):
    def test_parse_checkout_sessions_extracts_customer_and_subscription(self) -> None:
        events = parse_checkout_sessions(
            {
                "data": [
                    {
                        "created": 1_743_235_200,
                        "amount_total": 9_900,
                        "currency": "usd",
                        "customer_details": {"email": "buyer@example.com"},
                        "payment_status": "paid",
                        "status": "complete",
                        "mode": "subscription",
                        "subscription": {"id": "sub_123"},
                        "payment_link": "plink_123",
                    }
                ]
            }
        )
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].customer_email, "buyer@example.com")
        self.assertEqual(events[0].subscription_id, "sub_123")
        self.assertEqual(events[0].currency, "USD")


if __name__ == "__main__":
    unittest.main()
