# Agency Radar Outbound Playbook

## Goal

Turn one generated report into the first paid recurring brief.

## Sequence

1. Run:

   ```bash
   PYTHONPATH=src python3 -m agency_radar.cli build-site
   PYTHONPATH=src python3 -m agency_radar.cli prospects --profile federal_it --top 12
   PYTHONPATH=src python3 -m agency_radar.cli pitch-batch --profile federal_it --top 5 --sample-report-url https://your-public-url/sample-report.html
   ```

2. Publish the `docs/` directory so the sample report and catalog have public URLs.
3. Start with the top 5 generated pitch files in [`reports/pitches/federal_it/`](../reports/pitches/federal_it/).
4. Sell the weekly brief, not the codebase and not a dashboard.

## Offer

- `$99/month`: one weekly report
- `$249/month`: weekly report plus custom watchlist
- `$499/month`: two niches plus delivery customization

## Positioning

Use one concrete line:

`I built a narrow federal spend monitor that shows who is winning contracts, which agencies are spending, and which awards are expiring soon in your niche.`

## First Buyers

Prioritize:

- capture consultants
- small federal IT contractors
- subcontractors trying to team under primes
- niche MSPs entering federal work

Avoid opening with giant integrators unless a warm path exists.
