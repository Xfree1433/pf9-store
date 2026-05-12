# PF9 Affiliate Program Operations Playbook

**Program landing page:** `/refer/index.html` (live, public)
**Goal:** structured, low-overhead way to track referrals and pay commissions until volume justifies dedicated affiliate software (PartnerStack, Rewardful, etc.).

**Manual-first design:** at low volume, a Google Sheet + Stripe + PayPal/ACH covers everything. Defer tooling until 10+ active affiliates.

---

## Onboarding flow (when a signup arrives)

A new affiliate signup appears as a HubSpot Contact with product tag `AFFILIATE_PROGRAM_SIGNUP`. They land without a list assignment (the existing `_hubspot_list_for_product` returns None for this tag — that's intentional; create a "Affiliates" list manually if you want segmentation later).

Within one business day:

1. **Review the application** — check the `message` field for their stated channel. Disqualify obvious bad fits (coupon sites, brand-bidders, cold-email spam).
2. **Assign a referral code** — short, lowercase, memorable: their first name, podcast name, or company. e.g., `alex`, `modernmfg`, `kennedy`. Avoid generic words.
3. **Add them to the affiliate tracking sheet** (template below).
4. **Send the partner agreement + welcome email** (template below).

---

## Affiliate tracking sheet template

Create a Google Sheet named "PF9 Affiliates" with two tabs.

### Tab 1: Affiliates

| Code | Name | Email | Channel | Signed agreement? | Joined | Payout method | Notes |
|---|---|---|---|---|---|---|---|

### Tab 2: Referred Customers

| Affiliate code | Customer email | Customer name | Product | Monthly $ | Subscribed | Status | Commission/mo | Months paid | Total paid YTD |
|---|---|---|---|---|---|---|---|---|---|

**Status values:** Active, Refunded (14-day window), Churned, Past-12-months.

Update monthly by cross-referencing Stripe subscriptions against attribution.

---

## Attribution process

Until URL-capture infrastructure is built, attribution is manual:

1. **Customer mentions the affiliate at signup** — easiest. Watch for this in the `company` field or any notes on Stripe checkout. Add a public note on the storefront: "Mentioning a referral code? Add it to the company field when you subscribe."
2. **Customer subscribes within 90 days of clicking a `?ref=X` link** — currently relies on the affiliate telling you they referred someone. Won't scale, but works at low volume.
3. **Affiliate flags the referral** — they tell you "I sent Tom from AcmeCorp your way last week" and Tom appears in Stripe. Match manually.

When unsure, give the affiliate the benefit of the doubt. The relationship matters more than the $20–$60 commission.

**To upgrade attribution later:** ~2 hours of engineering — capture `?ref=` URL param to localStorage on storefront, include in Stripe checkout metadata, expose attribution in `store_api.py` `_handle_checkout_completed`. Defer until 5+ affiliates.

---

## Quarterly payout process

Run on the first business day of January, April, July, October. ~30 minutes.

1. **Pull Stripe subscriptions** for the previous quarter — note new subscriptions, active subscriptions, cancellations.
2. **Cross-reference against the tracking sheet** — mark each referred customer's status and update commission column.
3. **Calculate per-affiliate totals** — 20% of monthly subscription × months active in the quarter.
4. **Apply rules:**
   - Skip refunded customers (no commission)
   - Cap commissions at 12 months from first paid subscription
   - Roll over balances below $50 to the next quarter
5. **Send payouts** via ACH or PayPal.
6. **Send each affiliate an attribution summary** (template below).

---

## Email templates

### Welcome / partner agreement send

**Subject:** Welcome to the PF9 partner program — your code is `{code}`

```
Hi {name},

Welcome to the PF9 affiliate program. Your unique referral code is:

  {code}

People can use it two ways:
  1. Direct link: https://store.plainspokenfoundrynine.com/?ref={code}
  2. Mentioning the code at signup (in the "company" field works)

Attached: the one-page partner agreement. Sign and send back when convenient — we'll start tracking referrals as soon as you do.

The terms in 30 seconds:
- 20% of monthly subscription revenue, every month, for 12 months per referred customer
- Quarterly payouts via {ACH | PayPal}, $50 minimum
- 90-day attribution window from click or mention
- No commission on customers who refund within the 14-day guarantee

Questions on anything? Reply here. I read every email.

— Kennedy
Plainspoken Foundry Nine
```

### Quarterly payout email

**Subject:** PF9 affiliate payout — Q{N} {YEAR}

```
Hi {name},

Quarterly payout summary for Q{N}:

ACTIVE REFERRALS:
{For each active referred customer: customer email • product • months paid this quarter • commission}

NEW REFERRALS THIS QUARTER:
{Same format}

CHURNED OR REFUNDED:
{Same format with reason}

  Total Q{N} commission: ${X}
  Carryover from previous quarter: ${Y}
  Total payout: ${X+Y}

Payment method: {ACH to account ending {last4} | PayPal at {email}}
Expected receipt: {date}

Thanks for the referrals. Anything I can do better on the program side — let me know.

— Kennedy
```

### Quarterly "no payout this quarter" email

**Subject:** PF9 affiliate Q{N} — no payout this quarter

```
Hi {name},

No new active referrals this quarter, so no payout went out today.

If you had referrals you expected to be tracked — reply and I'll dig in. It's possible someone subscribed and didn't mention your code; we can sometimes match retroactively.

You're still in the program. Code: {code}

— Kennedy
```

### Disqualification email

**Subject:** PF9 affiliate program — terminating partnership

```
Hi {name},

I have to terminate your affiliate partnership. Reason: {specific disqualifying behavior, e.g. brand-bidding on "plainspokenfoundrynine"}.

Per the partner agreement, this means I'm not paying out commissions for referrals from {date} forward. Active referrals that converted before {date} will receive their remaining quarterly commissions through the 12-month window.

I'd rather not have done this. Happy to discuss if you think I'm reading the situation wrong.

— Kennedy
```

---

## Disqualification checks

Run these monthly. ~15 minutes.

- **Google search "plainspokenfoundrynine" + the affiliate's domain or business name** — looking for brand-bidding ads
- **Spam complaints** — any "I got an unsolicited cold email mentioning your product" replies
- **Self-referral check** — is the customer email tied to the same domain or company as the affiliate?
- **Bulk activity** — did the affiliate suddenly generate 50 referrals in a month with no traceable source? (Probable bulk-email or fake accounts)

Disqualify on confirmed violation. Reclaim unpaid commissions. Send the termination email.

---

## When to upgrade the program

**Move to dedicated affiliate software when:**

- 10+ active affiliates and the Google Sheet is becoming a tax
- 50+ referred customers and you can't reliably attribute by hand
- Affiliates are asking for self-serve dashboards / live attribution

**Options at that point:**

- **Rewardful** (~$49/mo) — built for SaaS, integrates with Stripe directly, low-friction affiliate dashboards
- **PartnerStack** (enterprise pricing) — more featured but priced for scale
- **Tolt** (~$29/mo) — newer, simpler

Until then, the Google Sheet is fine.

---

## Compliance notes

- **1099-NEC reporting** — for US-based affiliates earning over $600 in a calendar year, issue a 1099-NEC by January 31 of the following year. Collect W-9s at onboarding so you have what you need at year-end.
- **International affiliates** — no 1099 required for non-US affiliates. Pay via PayPal in their local currency or USD per their preference.
- **FTC disclosure** — affiliates must disclose the relationship when promoting (e.g., "I get a commission if you sign up through my link"). Required for US-based affiliates promoting to US audiences. Mention this in the welcome email.

---

## What I (the agent) can help with

- Draft attribution-capture infrastructure when the program grows (URL `?ref=` capture + localStorage + Stripe metadata pipeline)
- Write a custom quarterly payout email template per situation
- Build a `/refer/dashboard.html` if affiliates start asking for self-serve attribution (not in scope at v1)
- Update the program terms or commission structure if pricing changes
