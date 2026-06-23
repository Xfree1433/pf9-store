# Google Ads — Property Test Launch Runbook

**Your decision (2026-06-03):** start paid with a **test budget (~$300–500/mo)**, **property vertical first.**

This is the click-by-click execution doc for exactly that. It assumes nothing about prior Google Ads experience. `PLAYBOOK_GOOGLE_ADS.md` remains the strategy source of truth — this runbook just sequences the mechanical steps for the property-only test and points back to it for the deep parts.

**The number:** **$15/day on the Property campaign only** = ~$456/mo. That's the top of your range and matches the playbook's per-campaign recommendation. If you want the bottom of the range instead, use **$10/day** (~$304/mo) — both are fine; $15 gets you statistically real data faster.

**Manufacturing stays off.** You're testing one vertical so the signal is clean and the budget isn't split. Manufacturing campaign stays paused at $0 until property proves out.

---

## The one rule that matters most

**Set up conversion tracking BEFORE you spend a dollar.** If you launch ads without it, you're buying clicks blind — you'll have no idea which keywords produce leads or sales, and the whole "test to learn" purpose collapses. This is step 1 below, not an afterthought.

---

## ⚠️ Step 0 — Avoid Google's onboarding auto-create trap

**This bit you on 2026-06-20** (~$4 of accidental spend). It's a known Google dark pattern, not a one-off mistake — assume it will try again on any new Google Ads account.

**What Google does:** during account signup, the setup wizard pushes you into a "create your first campaign" flow. If you click through it (even just to reach billing setup), Google will auto-create a live Search campaign with:
- An auto-generated name like "Property" or "Sales" (no PF9 prefix)
- One ad group called "Ad group 1" with broad-match keywords (the worst match type)
- One AI-written ad based on whatever Google scraped from your landing page
- A "recommended" daily budget (usually $10–$30/day) **already enabled and spending**

It doesn't ask you to confirm before going live. It just goes live.

**What to do:**

1. During account signup, **refuse every "create your campaign" prompt.** Pick "Switch to Expert Mode" if offered, then close any campaign-creation modal. You only want billing set up at this stage, nothing else.
2. Immediately after the account is created, go to **Campaigns** in the left nav. If you see ANY campaign there (even one named generically like "Property" or "Sales"), it was auto-created — **delete it** before doing anything else. Campaigns → click campaign → menu (⋮) → **Remove**.
3. Then proceed to Step 1.

**The tell that you got caught by this:** any campaign you didn't import yourself from the CSV bundle, or any campaign with name that doesn't start with `PF9 -`. Don't try to salvage these — they're broad-match LANDLORDR/homepage ads that don't match your competitor-comparison strategy. Delete and re-import.

---

## Step 1 — Conversion tracking first (~20 min, blocking)

You already have GA4 firing the right events (`purchase`, `checkout_started`, `subscribe_modal_open`). You just need to pipe them into Google Ads.

1. Create a Google Ads account if you don't have one: https://ads.google.com → sign in with the Google account that owns your GA4 property → **switch to Expert Mode** if prompted → set up billing only. **Do not create a campaign** — see Step 0 above for why and how to refuse the prompts. If you already created the account and a "Property"/"Sales" campaign appeared, delete it per Step 0 before continuing.
2. **Link GA4 → Google Ads:** GA4 → Admin → Product Links → **Google Ads links** → Link → select your Ads account → confirm.
3. **Import the conversions:** Google Ads → Tools → **Conversions** → New conversion action → **Import** → Google Analytics 4 properties → select and import:
   - `purchase` — set priority **Primary**
   - `checkout_started` — set as **Secondary**
   - `subscribe_modal_open` — set as **Secondary**
   - (leave `video_play` unimported — it's gameable by junk traffic)
4. **Verify:** Tools → Conversions should list all three with a status that resolves to a green ✓ within a few hours (it says "No recent conversions" until traffic flows — that's normal pre-launch).

Full detail: `PLAYBOOK_GOOGLE_ADS.md` § Conversion tracking + the pre-launch checklist at the top.

---

## Step 2 — Import the property campaign (~10 min)

1. Download **Google Ads Editor** (free desktop app): https://ads.google.com/intl/en_us/home/tools/ads-editor/
2. Sign in with the account from Step 1.
3. Import these files from `tools/google-ads/` **in this order** (Account → Import → Paste text or Import CSV):
   - `campaigns.csv` first
   - `ad-groups.csv` second
   - `keywords.csv` and `ads.csv` third
4. Everything imports as **Paused** with **$0 budget** — that's the safety gate. Nothing spends yet.
5. Add the negative keyword list separately: Tools → Shared Library → Negative keyword lists → import `negatives.csv`.
6. **Post changes** to push to Google Ads.
7. **Verify in the Google Ads web UI** — go to **Campaigns**. You should see **exactly two** campaigns, both Paused, both $0:
   - `PF9 - Property Comparisons` (Search type, 3 ad groups: Buildium, AppFolio, DoorLoop)
   - `PF9 - Manufacturing Comparisons` (Search type, 3 ad groups: MRPeasy, Katana, Fishbowl)
   If you see a **third campaign** with a different naming pattern (e.g. just "Property", "Sales", "Ad group 1" content), it's a leftover from Google's onboarding auto-create — delete it now per Step 0 before continuing.

Both PF9 campaigns come in. That's fine — you'll only enable Property.

---

## Step 3 — Configure and enable Property ONLY (~5 min)

1. In Google Ads (web, not Editor), open the **PF9 - Property Comparisons** campaign.
2. Set **Daily budget = $15** (or $10 for the low end of your range).
3. Leave bid strategy on **Manual CPC** (the playbook's first-14-days recommendation — don't let Smart Bidding optimize against zero data).
4. Confirm the three ad groups (Buildium, AppFolio, DoorLoop) and their ads are present and set to **Enabled**.
5. Set campaign status to **Enabled**.
6. **Leave PF9 - Manufacturing Comparisons at Paused / $0.** Do not touch it.
7. Add sitelink/callout extensions manually (5 min) — copy from `PLAYBOOK_GOOGLE_ADS.md` § Sitelinks / Callouts. Not required to launch, but lifts CTR meaningfully.

You're now live.

---

## Step 4 — First 7 days: watch, don't tinker

- **Don't change budgets or bids for 7 days.** Early data is noisy; reacting to it burns money.
- **Daily (5 min):** check spend didn't run away and no ad group is getting zero impressions.
- **Day 3–4:** Reports → Search terms. Look at the actual queries triggering your ads. Add anything irrelevant (job listings, "free", competitor support pages) to the negative list. This is the highest-leverage 30 min of the week.
- Watch GA4 Realtime + HubSpot for leads attributed to the `google / cpc` source.

---

## What to realistically expect

At $15/day on property-only competitor terms (blended CPC ~$3):

| Metric | Realistic range |
|---|---|
| Clicks | ~5/day, ~150/mo |
| `subscribe_modal_open` (lead intent) | ~1–2/day |
| Paid subscriptions | bursty — could be 0 for two weeks then 1–2; B2B windows are days/weeks, not minutes |
| CAC (cost per subscription) | $50–$300 |

**The point of this spend is information, not immediate ROI.** After 2–4 weeks you'll know: does property convert, which competitor term is cheapest (Buildium vs AppFolio vs DoorLoop), and what your real cost-per-lead is. That turns the decision to scale (or pivot to manufacturing) into math instead of a guess.

---

## Kill criteria (from the playbook — these are real, not hedges)

**Pause an ad group** if after 14 days: ≥$100 spent, zero `checkout_started`, zero `purchase`, CTR below 1%.

**Pause the whole property campaign** if after 30 days: ≥$500 spent, zero `purchase`, and the CAC math can't work.

If property dies on these criteria, the test did its job — you spent ≤$500 to learn property-paid doesn't work at this price, and you redirect to manufacturing or another channel.

---

## What I (the agent) can do

- Tune the keyword list or ad copy if the search-terms report shows waste
- Write the manufacturing-test runbook when you're ready to expand
- Adjust the comparison landing pages if a specific competitor term drives traffic that bounces
- Draft the negative-keyword additions once you share the first search-terms report

## What I cannot do

- Create or access your Google Ads account, link GA4, or import the CSVs (your account/credentials)
- Spend money or enable campaigns on your behalf
- See your live ad performance — paste me the search-terms report or a screenshot and I'll analyze it
