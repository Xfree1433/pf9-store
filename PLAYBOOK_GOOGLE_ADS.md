# PF9 Google Ads Playbook

**Goal:** drive high-intent buyers to the storefront via paid search on competitor-comparison terms. Funnel them through the comparison pages → calculators or videos → Stripe.

**Why now:** the 6 comparison pages (`/comparisons/`) and 2 calculators are tailor-made landing destinations for buyers actively shopping. Without paid traffic these pages take months to rank organically. Paid skips the wait.

**Realistic expectation:** you're not buying leads, you're buying *test cycles*. First 14 days = data gathering. First conversion: weeks 2–3. First profitable campaign: month 2 if signal is strong.

---

## Pre-flight checklist

Before launching anything, confirm:

- [ ] **Google Ads account created** at https://ads.google.com (skip the "smart campaign" guided setup — you want **Expert mode**)
- [ ] **GA4 property linked** — GA4 → Admin → Product Links → **Google Ads links** → link the Ads account. Required for conversion import.
- [ ] **Conversions imported from GA4** — Google Ads → Tools → Conversions → New conversion action → **Import** → Google Analytics 4 properties → select these events:
  - `purchase` (Stripe success — set as **Primary** conversion)
  - `subscribe_modal_open` (high-volume soft signal — **Secondary**)
  - `checkout_started` (mid-funnel — **Secondary**)
- [ ] **Payment method on file** in Google Ads
- [ ] **Daily budget cap set on the account level** as belt-and-suspenders (e.g., $100/day account-wide so a runaway campaign can't drain you)

---

## Campaign architecture

**Two campaigns, six ad groups.** Tight match between keywords and the matching comparison page.

```
Campaign: PF9 — Property Comparisons
├── Ad group: Buildium      → /comparisons/buildium-vs-pf9.html
├── Ad group: AppFolio      → /comparisons/appfolio-vs-pf9.html
└── Ad group: DoorLoop      → /comparisons/doorloop-vs-pf9.html

Campaign: PF9 — Manufacturing Comparisons
├── Ad group: MRPeasy       → /comparisons/mrpeasy-vs-pf9.html
├── Ad group: Katana        → /comparisons/katana-vs-pf9.html
└── Ad group: Fishbowl      → /comparisons/fishbowl-vs-pf9.html
```

**Why two campaigns, not one big one:** budget control. You can pause the property campaign without touching manufacturing, and vice versa. Ad-group-level analytics stay clean.

**Why six ad groups, not three:** keyword-to-landing-page tightness. A buyer searching "buildium alternative" should land on the Buildium page, not a generic property page. Quality Score depends on this match.

---

## Campaign settings (apply to both campaigns)

| Setting | Value | Why |
|---|---|---|
| Campaign type | **Search** | Comparison-shoppers use search, not display |
| Networks | Google Search only — **uncheck** Search Partners and Display Network | Quality of partner traffic is poor for SaaS |
| Locations | **United States** (start) | Pricing in USD; expand to EN-Canada/UK after first conversion data |
| Languages | English | Match your storefront |
| Bidding strategy | **Manual CPC** for first 14 days | You don't have enough conversion data for Smart Bidding to work |
| Daily budget | **$15/day per campaign** ($30 total to start) | Affordable test; scale with what works |
| Ad rotation | **Optimize: prefer best performing ads** | Standard |
| Ad schedule | All hours, all days, B2B targeting bias toward weekday business hours | Optional refinement after week 2 |
| Devices | **Desktop bid +30%, Mobile −20%** initially | B2B comparison shoppers research on desktop, scroll on mobile |
| Negative keywords list | Apply the master list (see below) | Critical — saves significant waste |

---

## Keywords by ad group

All keywords use **phrase match** unless marked `[exact]`. Phrase match gives you reach without the noise of broad match.

### Property campaign

#### Ad group: Buildium → `/comparisons/buildium-vs-pf9.html`

```
"buildium alternative"               [exact]
"alternative to buildium"            [phrase]
"buildium pricing"                   [phrase]
"buildium per unit fee"              [phrase]
"buildium vs"                        [phrase]
"cheaper than buildium"              [phrase]
"buildium replacement"               [phrase]
"buildium for small landlord"        [phrase]
"buildium 50 units"                  [phrase]
"buildium competitor"                [phrase]
```

**Suggested max CPC:** $3.50

#### Ad group: AppFolio → `/comparisons/appfolio-vs-pf9.html`

```
"appfolio alternative"               [exact]
"appfolio under 50 units"            [exact]
"appfolio 50 unit minimum"           [phrase]
"appfolio for small landlord"        [phrase]
"appfolio pricing"                   [phrase]
"alternative to appfolio"            [phrase]
"appfolio competitor"                [phrase]
"cheaper than appfolio"              [phrase]
"appfolio core minimum"              [phrase]
```

**Suggested max CPC:** $4.00 (AppFolio terms tend to be more expensive — established mid-market vendor)

#### Ad group: DoorLoop → `/comparisons/doorloop-vs-pf9.html`

```
"doorloop alternative"               [exact]
"doorloop pricing"                   [phrase]
"doorloop pro pricing"               [phrase]
"doorloop 10 unit cap"               [phrase]
"doorloop vs"                        [phrase]
"alternative to doorloop"            [phrase]
"doorloop competitor"                [phrase]
"cheaper than doorloop"              [phrase]
"doorloop monthly billing"           [phrase]
```

**Suggested max CPC:** $3.00

### Manufacturing campaign

#### Ad group: MRPeasy → `/comparisons/mrpeasy-vs-pf9.html`

```
"mrpeasy alternative"                [exact]
"alternative to mrpeasy"             [phrase]
"mrpeasy pricing per user"           [phrase]
"mrpeasy vs"                         [phrase]
"mrp software no per user fee"       [phrase]
"cheaper than mrpeasy"               [phrase]
"mrpeasy competitor"                 [phrase]
"mrpeasy starter pricing"            [phrase]
```

**Suggested max CPC:** $2.50

#### Ad group: Katana → `/comparisons/katana-vs-pf9.html`

```
"katana mrp alternative"             [exact]
"katana mrp pricing"                 [phrase]
"katana vs"                          [phrase]
"alternative to katana mrp"          [phrase]
"katana mrp per user"                [phrase]
"katana mrp competitor"              [phrase]
"cheaper than katana mrp"            [phrase]
"katana standard pricing"            [phrase]
```

**Suggested max CPC:** $2.50

#### Ad group: Fishbowl → `/comparisons/fishbowl-vs-pf9.html`

```
"fishbowl inventory alternative"     [exact]
"fishbowl pricing"                   [phrase]
"fishbowl quickbooks alternative"    [phrase]
"fishbowl vs"                        [phrase]
"alternative to fishbowl inventory"  [phrase]
"fishbowl competitor"                [phrase]
"cheaper than fishbowl"              [phrase]
"fishbowl manufacturing pricing"     [phrase]
```

**Suggested max CPC:** $3.00

---

## Master negative keyword list

Add this as a **shared negative keyword list** (Tools → Shared Library → Negative keyword lists), then apply to both campaigns. Saves clicks from people who'll never convert.

```
"reviews"
"ratings"
"comparison chart"
"login"
"sign in"
"support contact"
"customer service"
"jobs"
"careers"
"salary"
"glassdoor"
"linkedin"
"crunchbase"
"wikipedia"
"what is"
"how does"
"how to use"
"tutorial"
"training"
"certification"
"api docs"
"documentation"
"integration guide"
"developer"
"github"
"open source"
"free download"
"crack"
"torrent"
"used"  // protects against "used buildium" referring to past use
```

**Property-only negatives** (apply to property campaign only — these terms collide with Buildium-the-software-company sometimes referring to Buildium-the-construction-term):

```
"construction"
"contractor"
"swimming pool"
"hot tub"
"plumbing"
```

**Manufacturing-only negatives:**

```
"katana sword"        // Katana brand collides with Japanese sword
"fishbowl game"       // Fishbowl game / drinking game
"fishbowl pet"        // Fishbowl as in goldfish bowl
```

---

## Ad copy — Responsive Search Ads

Each ad group needs **one Responsive Search Ad** with multiple headlines and descriptions. Google rotates them and learns which combinations win.

**Template per ad:**
- Up to 15 headlines (30 chars each)
- Up to 4 descriptions (90 chars each)
- Path 1, Path 2 fields show as part of the visible URL
- Sitelinks, callouts, structured snippets at the campaign level

### Buildium ad

**Final URL:** `https://store.plainspokenfoundrynine.com/comparisons/buildium-vs-pf9.html`
**Display path:** `/comparisons/buildium-vs-pf9`

**Headlines (15 max — Google picks combinations):**
1. Buildium Alternative — $119/mo Flat
2. Skip Per-Door Fees Forever
3. Buildium vs PF9: Honest Compare
4. 5–50 Units? Save vs Buildium
5. PF9 Property Suite, Flat $119
6. Unlimited Units, One Flat Price
7. Real Buildium Pricing Compare
8. 14-Day Money-Back Guarantee
9. Stop Paying $1.50/Unit/Month
10. Cancel Anytime, No Contract
11. Better Than Buildium for 5–50 Units
12. PF9 Property Suite Comparison
13. Buildium Replacement, Flat Rate
14. Per-Door Calculator Inside
15. Watch 90-Sec Demo on YouTube

**Descriptions (4 max):**
1. $119/mo flat for unlimited units. Honest comparison vs Buildium with pricing, features, and migration walkthrough.
2. Where Buildium wins, where PF9 wins, and the math at your portfolio size. Free per-door calculator inside.
3. 14-day money-back guarantee. Cancel anytime. Deploy in an afternoon. See why landlords are switching to flat pricing.
4. Watch the 90-second product demo on YouTube. No signup, no sales call. Then subscribe in 60 seconds.

### AppFolio ad

**Final URL:** `https://store.plainspokenfoundrynine.com/comparisons/appfolio-vs-pf9.html`

**Headlines:**
1. AppFolio Alternative for <50 Units
2. AppFolio Won't Sell Below 50 Units
3. PF9 Property Suite — $119/mo Flat
4. AppFolio Core Minimum: Skip It
5. No 50-Unit Minimum, No Quote
6. Real AppFolio Pricing Compare
7. AppFolio vs PF9: Honest Compare
8. Unlimited Units, $119/mo Flat
9. 14-Day Money-Back Guarantee
10. Cancel Anytime, No Contract
11. AppFolio Replacement for Small Landlord
12. PF9 — Built for 5–50 Unit Landlords
13. Skip the AppFolio Sales Call
14. Per-Door Calculator Inside
15. Watch 90-Sec Demo, No Signup

**Descriptions:**
1. AppFolio requires 50+ units. PF9 starts at 1. Honest comparison with pricing, features, and migration notes.
2. $119/mo flat — no per-unit fees, no minimum spend, no quote required. Subscribe in 60 seconds.
3. Where AppFolio wins (marketing, AI leasing) and where PF9 wins (flat pricing, no minimum, deploy in an afternoon).
4. 14-day money-back guarantee. Cancel anytime. Watch the 90-second demo on YouTube — no signup needed.

### DoorLoop ad

**Final URL:** `https://store.plainspokenfoundrynine.com/comparisons/doorloop-vs-pf9.html`

**Headlines:**
1. DoorLoop Alternative — Flat Pricing
2. No 10-Unit Cliff — Stay at $119/mo
3. DoorLoop vs PF9: Honest Compare
4. PF9 Property Suite — $119/mo Flat
5. Skip the DoorLoop Tier Break
6. 11+ Units? Save vs DoorLoop Pro
7. No Annual Contract, Cancel Anytime
8. Real DoorLoop Pricing Compare
9. Unlimited Team Members Included
10. 14-Day Money-Back Guarantee
11. DoorLoop Replacement, Flat Rate
12. Watch 90-Sec Demo, No Signup
13. Per-Door Calculator Inside
14. Built for 5–50 Unit Landlords
15. Stop Paying $189/mo for 11 Units

**Descriptions:**
1. DoorLoop's Pro tier kicks in at 11 units. PF9 stays $119/mo at any size. Honest comparison inside.
2. Where DoorLoop wins (built-in payments, polished UI) and where PF9 wins (flat pricing, no contract).
3. $119/mo flat for unlimited units, unlimited team members. No annual contract. 14-day money-back.
4. Watch the 90-second demo on YouTube. Subscribe in 60 seconds. Cancel anytime.

### MRPeasy ad

**Final URL:** `https://store.plainspokenfoundrynine.com/comparisons/mrpeasy-vs-pf9.html`

**Headlines:**
1. MRPeasy Alternative — $249 Flat
2. Stop Paying $49 Per User Per Month
3. MRPeasy vs PF9: Honest Compare
4. PF9 Manufacturing Suite, Flat
5. 6+ Users? Save vs MRPeasy
6. 5 Apps. Unlimited Users. $249/mo
7. No Per-Seat Fees Ever
8. Real MRPeasy Pricing Compare
9. Shifts, Inventory, Quality, More
10. 14-Day Money-Back Guarantee
11. MRPeasy Replacement, Flat Rate
12. Per-User Calculator Inside
13. Watch 5 Demos, No Signup
14. Built for Shops 20–250 Employees
15. Cancel Anytime, No Contract

**Descriptions:**
1. MRPeasy charges $49/user/mo. PF9 is $249/mo flat for unlimited users. Honest comparison inside.
2. Where MRPeasy wins (real MRP planning, BOMs) and where PF9 wins (flat pricing, broader operational coverage).
3. $249/mo for 5 apps: shifts, inventory, quality, dashboards, inspections. No per-seat fees ever.
4. Watch 5 product demos on YouTube. Subscribe in 60 seconds. 14-day money-back guarantee.

### Katana ad

**Final URL:** `https://store.plainspokenfoundrynine.com/comparisons/katana-vs-pf9.html`

**Headlines:**
1. Katana MRP Alternative — Flat Rate
2. Skip Katana's Tier Breaks
3. Katana vs PF9: Honest Compare
4. PF9 Manufacturing Suite, $249 Flat
5. 5 Apps Unlimited Users $249/mo
6. No Per-Seat Fees Ever
7. Real Katana Pricing Compare
8. Stop Paying $799 for 10 Users
9. 14-Day Money-Back Guarantee
10. Shifts, Inventory, Quality Inside
11. Katana Replacement, Flat Rate
12. Per-User Calculator Inside
13. Watch 5 Demos, No Signup
14. Built for 20–250 Employee Shops
15. Cancel Anytime, No Contract

**Descriptions:**
1. Katana's tiers break at every team size. PF9 is $249/mo flat. Honest comparison inside.
2. Where Katana wins (Shopify-Xero sync, BOM workflows) and where PF9 wins (flat pricing, shop-floor ops).
3. $249/mo for 5 apps: shifts, inventory, quality, dashboards, inspections. Unlimited users included.
4. Watch 5 product demos on YouTube. Subscribe in 60 seconds. 14-day money-back guarantee.

### Fishbowl ad

**Final URL:** `https://store.plainspokenfoundrynine.com/comparisons/fishbowl-vs-pf9.html`

**Headlines:**
1. Fishbowl Alternative — $249 Flat
2. Browser-Based, No Install
3. Fishbowl vs PF9: Honest Compare
4. PF9 Manufacturing Suite, Flat
5. Stop Paying $329+ Per Month
6. 5 Apps Unlimited Users $249/mo
7. No Per-Seat Fees Ever
8. Real Fishbowl Pricing Compare
9. 14-Day Money-Back Guarantee
10. Shifts Quality Inspections Inside
11. Fishbowl Replacement, Flat Rate
12. Per-User Calculator Inside
13. Watch 5 Demos, No Signup
14. Built for 20–250 Employee Shops
15. Cancel Anytime, No Contract

**Descriptions:**
1. Fishbowl is per-user from $329/mo. PF9 is $249/mo flat for unlimited users. Honest comparison inside.
2. Where Fishbowl wins (real-time QuickBooks sync) and where PF9 wins (flat pricing, browser-based, broader coverage).
3. $249/mo for 5 apps: shifts, inventory, quality, dashboards, inspections. No installation, no IT setup.
4. Watch 5 product demos on YouTube. Subscribe in 60 seconds. 14-day money-back guarantee.

---

## Sitelinks (apply at campaign level)

Sitelinks add additional clickable destinations under your ad. **Add these 6 to both campaigns:**

| Sitelink text | Description line 1 | Description line 2 | URL |
|---|---|---|---|
| Watch the Demos | All 14 product videos | 90 seconds each, no signup | https://www.youtube.com/@plainspokenfoundrynine |
| For Landlords | 5–50 units, flat $119/mo | Unlimited units & tenants | https://store.plainspokenfoundrynine.com/for-landlords.html |
| For Manufacturers | 20–250 employees | Flat $249/mo, unlimited users | https://store.plainspokenfoundrynine.com/for-manufacturers.html |
| Per-Door Calculator | See real cost vs Buildium | Free, no signup required | https://store.plainspokenfoundrynine.com/tools/per-door-calculator.html |
| Per-User Calculator | See real cost vs MRPeasy | Free, no signup required | https://store.plainspokenfoundrynine.com/tools/per-user-calculator.html |
| All Comparisons | Buildium, AppFolio, DoorLoop | MRPeasy, Katana, Fishbowl | https://store.plainspokenfoundrynine.com/comparisons/ |

## Callouts (apply at campaign level)

```
14-Day Money-Back
No Contract
Cancel Anytime
No Per-User Fees
Unlimited Users
Subscribe in 60 Seconds
Watch Demo, No Signup
Deploy in an Afternoon
```

## Structured snippets (apply at campaign level)

**Header:** Featured
**Values (property campaign):** LANDLORDR, TENANTLINK, Property Suite, Per-Door Calculator
**Values (manufacturing campaign):** FLOWTRACK, QUALIFI, SHIFTLOG, REPORTR, INSPECTR, Per-User Calculator

---

## Conversion tracking — what to optimize toward

In Google Ads, set conversion priorities:

| Conversion | Priority | Why |
|---|---|---|
| `purchase` (from GA4 → Stripe success) | **Primary** | Real revenue. Final goal. |
| `subscribe_modal_open` | **Secondary** (counts toward Conversions) | High volume early — bidding signal before purchases accumulate |
| `checkout_started` | **Secondary** | Mid-funnel intent |
| `video_play` | Track but don't optimize toward | Vanity-adjacent; easy to game by junk traffic |

**Bidding evolution:**
- **Days 1–14:** Manual CPC. You're not buying conversions yet, you're buying *learning data*. Don't let Smart Bidding optimize against zero data.
- **Days 14–30:** If you have ≥30 conversion events (any priority), switch to **Maximize Conversions**.
- **Day 30+:** If you have ≥50 `purchase` conversions, switch to **Target CPA** with target = your acceptable cost per subscription. Start with a CPA ceiling that makes economic sense given your monthly subscription value.

---

## Budget guidance

**Starting budget: $30/day total ($15 per campaign).**

This is a test budget, not a scale budget. With $30/day:
- ~10–25 clicks/day across both campaigns
- ~1–3 `subscribe_modal_open` events/day
- ~0.05–0.15 paid subscriptions/day (average — bursty in reality)

**Realistic CAC for these terms:** $50–$300 per subscription. The flat-rate value prop is strong, but B2B conversion windows are days/weeks not minutes.

**Scale rules:**
- Don't change budgets in the first 7 days. Let data accumulate.
- After 7 days, kill any ad group with zero clicks and reallocate to the top performer.
- After 14 days, double the budget on the top campaign (the one with the lowest CPA), keep the other flat.
- After 30 days, if total CAC < your monthly subscription value × 3, scale up by 50% per week.

**Red flags that mean pause everything:**
- Any single keyword burns >$50 with zero clicks-to-conversion (likely junk match)
- CPA exceeds 5× the monthly subscription value
- Click-through rate below 1% across all ads (relevance is broken — rewrite ads)

---

## Reporting cadence

**Daily (first 7 days):** check spend and quality score on each ad group. Catch runaway spend or zero-traffic keywords early.

**Weekly:** in Google Ads → Reports → Predefined → Search terms. Look at the actual queries triggering your ads. Add anything irrelevant to the negative keyword list. This is the most leveraged 30 minutes you'll spend per week.

**Bi-weekly:** review Quality Score per keyword. Anything below 5 means the ad-keyword-landing-page match is weak. Either rewrite the ad or pause the keyword.

**Monthly:** look at conversion attribution in GA4 (Admin → Attribution → Reports → Conversion paths). If most conversions are last-click on Google Ads, fine. If most conversions show Google Ads as an assist (not last-click), the channel is more valuable than the dashboard suggests.

---

## Kill criteria

Pause an ad group if all of these are true after 14 days:
- ≥$100 spent
- Zero `purchase` conversions
- Zero `checkout_started` conversions
- Click-through rate below 1%

Pause an entire campaign if all of these are true after 30 days:
- ≥$500 spent
- Zero `purchase` conversions
- CAC modeling can't make the math work

These are real kill criteria, not "let it run a bit longer" hedges. Bad campaigns burn money quietly.

---

## Pre-launch test plan

Before flipping the switch:

- [ ] Verify GA4 Realtime fires `subscribe_modal_open` and `checkout_started` events when you click through manually (already confirmed 2026-05-08, but re-verify after any storefront deploy)
- [ ] Verify Google Ads conversion import shows the GA4 events in Tools → Conversions with a green ✓ status
- [ ] Run **one** ad group (start with Buildium — established demand, predictable terms) for 24 hours at $5/day to validate clicks land on the right page and tracking fires
- [ ] Look at Search Terms report after 24 hours — confirm the queries triggering your ad are actually relevant
- [ ] If anything looks wrong: pause, fix, re-test before launching the other 5 ad groups

---

## What I (the agent) can help with later

- Write new ad copy variants when you want to test
- Add new keywords as you discover good queries in the search terms report
- Update negative keyword lists when junk traffic patterns emerge
- Write a Google Ads conversion-value setup if Stripe revenue varies meaningfully per product
- Build a small `tools/google-ads-utm-decoder.html` that translates UTM-tagged storefront URLs back to ad copy, if attribution gets complex
- Adjust bidding strategy when you cross conversion-volume thresholds

## What I (the agent) cannot do

- **Sign in to Google Ads** — account access required
- **Set bids in real-time** — no Google Ads MCP in this session
- **Generate ad images** — no image generation; sitelinks and ads above are text-only
- **Forecast guarantees** — CPC and conversion rates are dependent on competition and Quality Score, both of which are unknowable until you launch

---

## What I'm ready to do once you say go

If you tell me your starting daily budget and confirm you have the Google Ads account + GA4 link set up, I can:

1. Output a CSV that imports straight into Google Ads Editor with all 6 ad groups, keywords, ads, and negative keyword list pre-built — saves you 2 hours of clicking
2. Write a one-page launch checklist printable
3. Pre-write the Week 2 optimization actions (search-term review template, CPA targets to set)

Just say "build the Editor CSV" and I'll have it ready in 5 minutes.
