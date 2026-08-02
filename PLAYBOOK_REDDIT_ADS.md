# PF9 Reddit Ads Spec — Property-First Test

**Purpose:** a lower-risk paid channel. Written property-first to match the paid strategy (property vertical proves out before manufacturing).

**Why Reddit at all — updated 2026-08-02.** This originally read as a *hedge* against Google getting twitchy. It is no longer a hedge; **it is the only paid channel PF9 has left**, and it is unstarted. The corrected history, because the earlier version of this line conflated two separate suspensions:

- **2026-06-24 — first suspension.** Google cited "Unacceptable business practices (Phishing / Public figure impersonation / Other)." The working theory at the time was a competitor-keyword false positive, which is what this playbook was written against. Appealed; **reinstated.** Package kept at `APPEAL_GOOGLE_ADS_2026-06-24.md`.
- **~2026-07-26 — second suspension.** Same umbrella category, but Google named the specific policy this time: **Public Figure Impersonation.** The 2026-07-26 review found the flagged ad's 10 assets and the landing page both clean — no public figure anywhere — so this one was a false positive too. Appealed 2026-07-26.
- **2026-08-02 — account cancelled.** Google's ~5-business-day reply window passed with no answer and the account was cancelled rather than wait longer. `PLAYBOOK_GOOGLE_ADS.md` and `PLAYBOOK_GOOGLE_ADS_PROPERTY_TEST.md` are both marked dead.

So "if Google gets twitchy again" already happened, twice, and the second time it stuck. Reddit's remaining case stands on its own merits: different platform, different policy regime, much cheaper clicks, and an audience of exactly the small landlords/investors PF9 targets.

**Status: not started.** There is no `rdt(` pixel in the storefront HTML and no Reddit Ads account. The pixel step below is still blocking.

**Budget frame:** $10/day (~$300/mo). ⚠️ The "committed $300–500 range" this refers to was the budget for the **Google property test, which never launched** — there is no committed paid budget today (see `SALES_PLAN.md` §8). Treat $10/day as a proposal requiring a fresh spend decision, not an approved number. Reddit clicks are far cheaper than Google's (~$0.30–$1.50 vs $3+), so it does buy meaningfully more clicks per dollar.

---

## Reddit vs Google — what's different (set expectations)

| | Google Search | Reddit Ads |
|---|---|---|
| Buyer state | Actively searching for a fix | Scrolling their community, not shopping |
| Intent | High (typed "buildium alternative") | Lower — you interrupt, but in a relevant context |
| CPC | ~$3+ | ~$0.30–$1.50 |
| Creative | Text ad | Native post (image/video/text) — must not feel like an ad |
| Suspension risk | High (competitor keywords) | Low |
| Best content | Comparison pages | Honest "I built this" founder posts, calculators |

**Implication:** don't run Google's competitor-comparison ads verbatim on Reddit. Reddit's audience is ad-hostile and detects marketing instantly. The winning angle here is **honest, useful, founder-voice** — the same tone as the HN post, not a sales pitch.

---

## ⚠️ Prerequisite — install the Reddit Pixel FIRST (blocking)

Reddit has its own conversion pixel, separate from GA4 and PostHog. Without it, you're buying clicks blind — no idea which subreddit or ad drives leads.

1. Create the Reddit Ads account: https://ads.reddit.com → sign in / sign up.
2. **Events Manager → Reddit Pixel → create pixel** → copy the pixel base code + the `rdt('track', ...)` event snippet.
3. Install the pixel on the storefront:
   - Base pixel in `<head>` of all pages (same pattern as GA4/PostHog loaders)
   - Fire a `Lead` event on `subscribe_modal_open` and a `Purchase` event on the Stripe success page — mirror the existing GA4 event points
4. Verify with the **Reddit Pixel Helper** browser extension before spending.

**I (the agent) can wire this pixel into the storefront HTML directly** — same as GA4/PostHog were added — once you paste the pixel ID. That removes the blocking step. Just say "wire the Reddit pixel" and give me the ID.

---

## Account structure

One campaign, property-only, three ad groups by community cluster so you can see which audience converts cheapest.

```
Campaign: PF9 – Property (Reddit Test)
  Objective: Conversions (Lead) — or Traffic if pixel data is thin at first
  Daily budget: $10
  Ad groups:
    1. Landlords (community-targeted)
    2. Real-estate investors (community-targeted)
    3. Property managers (community-targeted)
```

Start all three at ~$3–4/day each. After 7 days, kill the weakest and reallocate.

---

## Targeting — exact subreddits

**Ad group 1 — Landlords**
```
r/Landlord
r/landlords
r/RealEstateInvesting  (overlaps — see below; keep in AG2 if you want cleaner reads)
```

**Ad group 2 — Real-estate investors**
```
r/realestateinvesting
r/RealEstate
r/PropertyDevelopment
```

**Ad group 3 — Property managers**
```
r/PropertyManagement
r/Rentals
r/RealEstateTechnology
```

Notes:
- Use **community targeting** (not just interest targeting) — it's the tightest fit and Reddit's most reliable signal.
- **Geo:** United States only (matches the product/pricing).
- **Exclude** r/personalfinance, r/legaladvice-style broad subs — too noisy.
- Avoid keyword/interest-only targeting for v1; community targeting keeps you in-context.

---

## Creative — Reddit-native ad drafts

Reddit ads live or die on not feeling like ads. All three below are written in founder voice, lead with a real problem, and disclose honestly. Each links to the matching landing page.

### Ad A — the per-door math (best all-rounder)
**Format:** image or text post
**Headline:** `I got tired of property software charging me per unit, so I built a flat-rate one`
**Body:**
```
Every tool I looked at — Buildium, AppFolio, DoorLoop — charged per door or had a unit minimum. At 50 units that's real money every month, and it goes up every time you grow.

PF9 Property Suite is $119/mo flat. Unlimited units, unlimited tenants. Leases, rent ledger, maintenance, vendor invoices, tenant portal.

Not saying it's better than the incumbents at everything — the comparison pages on the site literally list where they win. But if per-unit pricing has been eating your margin, the math is worth a look.

14-day money-back, no contract. Free per-door calculator on the site so you can run your own numbers.
```
**CTA:** `Learn More` → `https://store.plainspokenfoundrynine.com/for-landlords.html`

### Ad B — the calculator hook (highest utility, lowest "ad" feel)
**Headline:** `Free calculator: what you're actually paying per door vs a flat rate`
**Body:**
```
Made a small tool that takes your unit count and current software bill and shows the per-door math against a flat $119/mo. No email required to use it.

Built it because I could never get a straight per-unit number out of the big vendors' pricing pages.
```
**CTA:** `Learn More` → `https://store.plainspokenfoundrynine.com/tools/per-door-calculator.html`

### Ad C — the honest comparison (for the investor AG)
**Headline:** `Buildium/AppFolio/DoorLoop vs a flat-rate option — honest comparison, including where they win`
**Body:**
```
Put together side-by-side comparisons for the big property tools vs the flat-rate suite I built. Each page has a "where they do better" section — Buildium's accounting, AppFolio's leasing, DoorLoop's payments — because pretending otherwise is useless to anyone actually deciding.

Short version: if you're 5–50 units and per-door fees hurt, flat rate wins the math. If you need the deep features the incumbents spent 10 years building, they might be the call.
```
**CTA:** `Learn More` → `https://store.plainspokenfoundrynine.com/comparisons/`

**Creative production notes:**
- If using image ads: a clean screenshot of the per-door calculator or a simple "flat $119 vs stacking per-unit fees" chart outperforms stock photos.
- Video ads are allowed — your 90-second LANDLORDR/PROPERTY_BUNDLE YouTube demos can be trimmed to 15–30s vertical. Optional for v1; text/image is enough to start.

---

## Budget & bidding

- **Daily budget:** $10 total ($3–4 per ad group).
- **Bid strategy:** start with **Maximize conversions** only if the pixel already has data; otherwise **Maximize clicks / manual CPC** at ~$0.75 for the first week to gather data cheaply.
- **Objective:** if the Reddit pixel is fresh (no conversion history), run **Traffic** objective first for ~1 week, then switch to **Conversions (Lead)** once the pixel has fired enough events for Reddit to optimize.

---

## Launch sequence

1. ✅ Reddit Ads account created + billing set
2. ✅ Reddit Pixel installed on storefront + verified with Pixel Helper (blocking — see prerequisite)
3. Build 1 campaign, 3 ad groups, community targeting above
4. Load Ads A/B/C (rotate; A everywhere, B in landlord/investor AGs, C in investor AG)
5. Budget $10/day, US-only, Traffic objective to start
6. Launch. **Watch, don't tinker, for 7 days.**

---

## What to watch / weekly cadence

- **Day 3–4:** check CTR per ad. Reddit CTR benchmark is low (~0.3–0.5%); below 0.2% means the creative reads as an ad — rewrite.
- **Reddit comments on your ads.** Unlike Google, Reddit ads get *comments* — and they can be brutal. **Monitor and reply in founder voice.** A good-faith reply to a skeptical comment converts lurkers better than the ad itself. Never argue; concede real limitations.
- **Day 7:** kill the weakest ad group, reallocate to the best. Kill any ad below 0.2% CTR.

---

## Kill criteria

Pause the whole Reddit test if after **$300 spent (≈30 days)**:
- Zero `Lead` events (subscribe modal opens) attributable to Reddit, AND
- CTR below 0.2% across all ads after creative iteration

If Reddit produces leads but Google doesn't (or vice versa), that's the signal to concentrate budget on the winner.

---

## Reddit-specific tone rules (don't skip)

- **Never fake being a regular user.** These are labeled ads; own it. The "I built this" framing is honest because you did.
- **Concede limitations openly.** Reddit rewards it; hides nothing the comparison pages don't already say.
- **Reply to comments as the founder**, not a brand. First person.
- **No competitor bashing.** "Where they win" framing only. (Also lower policy risk.)
- **Don't reuse the exact Google competitor-keyword ad copy** — different platform norms, and it's the copy that got Google twitchy.

---

## What I (the agent) can do next

- **Wire the Reddit Pixel into the storefront HTML** (all pages + Lead/Purchase events) once you give me the pixel ID — removes the one blocking step
- Draft image-ad creative specs (the flat-vs-per-door chart) for a designer
- Write the manufacturing-vertical Reddit spec when property proves out
- Trim the YouTube demos into 15–30s vertical cuts spec for video ads

## What I cannot do

- Create/operate the Reddit Ads account or spend money (your account)
- Post or reply to Reddit comments on your behalf (your identity/reputation)
- Verify the pixel fires in production (you check with Pixel Helper on a real browser)
