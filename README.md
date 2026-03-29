# Agency Radar

Agency Radar is a low-capital product bet: a recurring procurement-intelligence feed built on open federal spending data.

The core idea is simple:

- pull a narrow market slice from USAspending
- summarize the highest-value agencies and recipients
- flag contracts expiring soon
- package the report into HTML, Markdown, and CSV
- sell the recurring intelligence to niche buyers

## Why This Product

This is closer to a money machine than a generic app because:

- the data source is public
- the pipeline can be automated
- the output can be sold as a recurring report
- the product can start with one niche and one buyer profile
- it does not require a marketplace approval before it can be useful

It is not fully passive from day one. Nothing from zero is. But it can become low-touch much faster than a service business.

## Current MVP

- config-driven buyer niches in [`config/profiles.json`](config/profiles.json)
- live award pulls from the official USAspending API
- summary analysis for top agencies, top recipients, expiring awards, and top recompete candidates
- change tracking for newly observed awards compared with the previous run
- static report generation to:
  - HTML
  - Markdown
  - CSV
  - JSON summary
- ranked buyer-target exports from live award data
- batch outreach draft generation for the highest-priority prospects
- publishable niche catalog in [`docs/catalog.html`](docs/catalog.html)
- buyer-specific outreach generation from live report data
- scheduled automation template in [`.github/workflows/build-report.yml`](.github/workflows/build-report.yml)
- landing page in [`docs/index.html`](docs/index.html)

## Quick Start

List profiles:

```bash
PYTHONPATH=src python3 -m agency_radar.cli list-profiles
```

Build a report:

```bash
PYTHONPATH=src python3 -m agency_radar.cli build --profile federal_it
```

Outputs land in [`reports/`](reports/).

Build the full public site catalog:

```bash
PYTHONPATH=src python3 -m agency_radar.cli build-site
```

That refreshes:

- [`docs/catalog.html`](docs/catalog.html)
- [`docs/reports/`](docs/reports/)
- [`docs/data/catalog.json`](docs/data/catalog.json)

Generate ranked buyer targets:

```bash
PYTHONPATH=src python3 -m agency_radar.cli prospects --profile federal_it --top 12
```

Generate a batch of outreach drafts:

```bash
PYTHONPATH=src python3 -m agency_radar.cli pitch-batch --profile federal_it --top 5 --sample-report-url https://agency-radar.example/sample-report.html
```

Generate a personalized outreach draft:

```bash
PYTHONPATH=src python3 -m agency_radar.cli pitch --profile federal_it --company "Acme Federal" --first-name Alex --sender-name Luke
```

## Productization Path

The fastest real monetization path is:

1. Pick one niche profile.
2. Generate one polished report.
3. Sell a weekly or daily version to a tiny group of buyers.
4. Add:
   - Slack delivery
   - email delivery
   - customized watchlists
   - SAM.gov opportunity data later

## Current Sales Assets

- pricing and positioning in [`docs/pricing.html`](docs/pricing.html)
- public niche catalog in [`docs/catalog.html`](docs/catalog.html)
- go-to-market notes in [`ops/go-to-market.md`](ops/go-to-market.md)
- launch blockers and minimal identity requirements in [`ops/launch-blockers.md`](ops/launch-blockers.md)
- outreach templates in [`templates/`](templates/)
- generated prospect sheets in [`reports/`](reports/)
- first-pass official contact surfaces in [`data/initial_outreach_contacts.csv`](data/initial_outreach_contacts.csv)

## Honest Constraint

This is a viable subscription engine, not magic. To get paid, we still need one of:

- outbound sales
- a niche audience
- a marketplace
- a referral loop

What this repo does is remove the heavy lifting from the product side so distribution becomes the only real problem left.
