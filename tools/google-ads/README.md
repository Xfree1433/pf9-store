# Google Ads Import Bundle

Pre-built CSVs that import directly into **Google Ads Editor** to spin up the 2 campaigns + 6 ad groups + 6 ads + 50+ keywords + ~40 negatives described in `PLAYBOOK_GOOGLE_ADS.md`. Saves ~2 hours of manual clicking.

> **Launching the first test?** Follow `../../PLAYBOOK_GOOGLE_ADS_PROPERTY_TEST.md` — the click-by-click runbook for the property-first test (decided 2026-06-03): conversion tracking first, then import, then enable the Property campaign only at $15/day. This README covers the mechanical import; that runbook sequences the whole launch.

## Files

| File | What it imports | Editor menu |
|---|---|---|
| `campaigns.csv` | 2 Search campaigns (Property + Manufacturing) | Account → Import → Paste text |
| `ad-groups.csv` | 6 ad groups, one per competitor | Account → Import → Paste text |
| `keywords.csv` | All 50+ keywords with match types | Account → Import → Paste text |
| `ads.csv` | 6 Responsive Search Ads (one per ad group) | Account → Import → Paste text |
| `negatives.csv` | Account-level negative keyword list | Tools → Shared Library → Negative keyword lists |

## How to import (10 minutes)

1. **Download Google Ads Editor** (free desktop app): https://ads.google.com/intl/en_us/home/tools/ads-editor/
2. Sign in with the Google account that owns your Ads account
3. **Import each CSV file** in this order — order matters because keywords/ads reference ad groups, and ad groups reference campaigns:
   - `campaigns.csv` first
   - `ad-groups.csv` second
   - `keywords.csv` and `ads.csv` third (either order)
   - `negatives.csv` last (separate workflow via Shared Library)
4. **Review the staged changes** — Editor shows everything as "pending" before pushing live
5. **Post changes** to push to Google Ads

## Important: budget is intentionally set to $0/day

Every campaign in `campaigns.csv` has `Daily budget` set to `0` so nothing spends until you intentionally turn it on. After importing:

1. Go to each campaign
2. Set the daily budget to whatever you can afford (recommended start: $15/day per campaign = $30/day total)
3. Set status to **Enabled** (campaigns import as **Paused**)

This is deliberate — accidentally launching a campaign at the wrong budget can burn hundreds of dollars before you notice.

## What's NOT in this bundle (and why)

- **Sitelink, callout, and structured snippet extensions** — Google Ads Editor's CSV format for extensions is finicky and varies by Editor version. Add these manually via the playbook copy in `PLAYBOOK_GOOGLE_ADS.md` § Sitelinks / Callouts / Structured snippets. 5 minutes.
- **Conversion tracking setup** — `PLAYBOOK_GOOGLE_ADS.md` § Conversion tracking covers the GA4 link + import steps. Do this before launching.
- **Smart bidding strategy** — campaigns import as Manual CPC per the playbook recommendation for the first 14 days. Switch to Smart Bidding (Maximize Conversions or Target CPA) after data accumulates.

## Field reference

CSV column names follow Google Ads Editor's expected headers. If Editor complains about a column header during import, check that you're on the latest Editor version — Google occasionally renames columns between versions.

## After import

See `PLAYBOOK_GOOGLE_ADS.md` for:

- Pre-launch test plan (run one ad group at $5/day for 24h before scaling)
- Reporting cadence (daily / weekly / monthly)
- Kill criteria (when to pause)
- Budget scale rules

The playbook is the source of truth for the strategy. This bundle is just a time-saver for the mechanical setup.
