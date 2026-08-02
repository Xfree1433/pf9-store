# PF9 App Store — Marketing & Sales Plan

**Prepared for:** Cowork
**Client:** Plainspoken Foundry Nine (PF9)
**Storefront:** https://store.plainspokenfoundrynine.com
**Engagement window:** 90 days, renewable — **never started, see below**
**Primary goal:** Move PF9 from "launch-complete" to repeatable, measurable monthly revenue.

> ## ⚠️ Status: unexecuted proposal (noted 2026-08-02)
>
> **This document describes an engagement that was never entered into.** `SOW_COWORK.md`
> (PF9-COWORK-001) still carries `**Effective date:** [DATE]` — the literal placeholder,
> unfilled since both files were written on 2026-04-18. The 90-day term runs "from Effective
> Date," so with no effective date there is no day 1, and the week-numbered phases in §5
> cannot be located on a calendar. Do not read "Weeks 4–8" as a deadline; it refers to a clock
> that was never started.
>
> **Read every "Cowork will / Cowork owns" statement as aspirational.** No agency is running
> this. The work that has actually happened was done in-house, and where it overlaps Phase 1
> it is genuinely done — 14/14 product videos are live, HubSpot is wired, the lifecycle flows
> are built in Klaviyo. Where it doesn't overlap, it is simply not happening: no outbound
> lists, no blog cadence, no weekly reporting, no SDR.
>
> The §7 KPI targets were sized against a funded 90-day agency engagement and a $5k/mo paid
> budget. Neither exists (see §8), so those numbers are not a scorecard anything is currently
> being measured against.
>
> Keep this doc if the agency conversation is ever revived — the ICPs, positioning guardrails
> and channel logic are still sound. Just don't mistake it for a plan in flight.

---

## 1. Engagement Scope

Cowork owns demand generation and sales motion for the PF9 App Store. Engineering and product copy stay in-house; Cowork brings the buyers and closes them.

**In scope**
- Paid and organic demand generation across the four product verticals
- Outbound sales motion (lists, sequences, calls, CRM hygiene)
- Conversion optimization on the existing storefront (copy + layout tests only — no re-platforming)
- Lifecycle email: trial → paid, paid → expand, churn-save
- Weekly pipeline + revenue reporting

**Out of scope**
- App feature development, pricing changes, new product lines
- Replacing the static HTML storefront or Stripe stack
- Any campaign that misrepresents flat-rate pricing or "no per-user fees" claims

---

## 2. Product & Pricing Map

Cowork should treat PF9 as **four distinct go-to-market motions**, not one. Each has a different buyer, buying cycle, and price point.

| Vertical | Apps | Price band | Motion |
|---|---|---|---|
| **Manufacturing suite** | FLOWTRACK $99, QUALIFI $79, SHIFTLOG $49, REPORTR $59, INSPECTR $49 — bundle $249/mo | $49–$249/mo | Mid-touch: content + outbound to plant managers |
| **AI Ops Intelligence** | OPSIQ ($79 / $199 / $399) | $79–$399/mo | Higher-touch: demo-led, operations VP buyer |
| **Property management** | LANDLORDR $89, TENANTLINK $49, TASKFLOW $69, PERMITR $299 — Property Suite (LANDLORDR + TENANTLINK) $119/mo | $49–$299/mo | Low-touch: self-serve, SEO. *(Paid search is no longer available — see §5.)* |
| **Compliance** | COMPLI (Free / Pro / Enterprise) | Freemium | PLG: free tier → Pro upgrade |
| **Consumer** | WEALTHWATCH (free desktop download) | Free lead magnet | Top-of-funnel only — not a revenue channel |

**Pricing differentiator to lead with everywhere:** flat monthly rate, no per-user fees, bundle at ~1/8 the cost of enterprise equivalents.

---

## 3. Ideal Customer Profiles

### ICP-1: Small-to-mid manufacturer (primary — 60% of effort)
- 20–250 employees, $5M–$100M revenue
- Discrete or light-process manufacturing
- Currently using Excel, paper travelers, or a legacy MES they hate
- Buyer: Plant Manager or Ops Director; economic buyer: Owner/GM
- Pain quote we own: *"We're manufacturers who got tired of being told we need a $50k ERP system to track parts and shifts."*

### ICP-2: Multi-site operations leader (OPSIQ — 20% of effort)
- VP Ops / COO at a 2–20 site operator (manufacturing, logistics, field services)
- Already has data in disparate systems; wants answers, not dashboards
- Buys on a demo, not a trial

### ICP-3: Independent landlord / small property manager (20% of effort)
- 5–200 units under management
- Price-sensitive, self-serve buyer
- Reached through SEO and paid search, not outbound

Cowork should explicitly **not** target enterprise (1,000+ employee) manufacturers or national multifamily operators — they'll ask for features PF9 deliberately doesn't build.

---

## 4. Positioning & Messaging Guardrails

**Master narrative:** Practical apps, flat pricing, deploy in minutes — built by operators for operators.

**Three proof pillars Cowork must hit in every asset:**
1. **Flat monthly price, no per-user fees** (always show the number)
2. **Live demo, no signup** (link to demo in every CTA)
3. **Deploy in minutes, not months** (counter the 3–6 month ERP timeline)

**Don't say**
- "Enterprise-grade" — we're deliberately not enterprise
- Competitor names by name in paid copy
- Anything implying AI replaces the operator (OPSIQ assists, it doesn't decide)

---

## 5. Channel Plan & 90-Day Calendar

### Phase 1 — Weeks 1–3: Foundation
- Audit storefront analytics; install missing events (`video_play`, `subscribe_modal_open`, `checkout_started`, `support_email_click`) if not present
- Set up CRM (HubSpot Free tier acceptable) with pipeline stages: MQL → Video Watched → Trial → Subscribed → Active / Churned
- Build 3 outbound lists (manufacturing, multi-site ops, property) — 500 contacts each
- Produce one 60–90-second product video per app, hosted on YouTube, embedded on each product card
- Repurpose existing MARKETING.md LinkedIn posts into a 4-week drip
- Rewrite storefront hero headlines per vertical; A/B test against current

### Phase 2 — Weeks 4–8: Launch motion
- **Paid:** 🛑 **no live paid channel as of 2026-08-02.** The original plan here read *"Google
  Search on long-tail manufacturing terms; LinkedIn ads targeted at Plant Manager / Ops
  Director at 50–500-employee manufacturers. Starting budget: $3k/mo Google, $2k/mo
  LinkedIn."* Neither half survived: **Google Ads was cancelled 2026-08-02** after a
  mis-categorized suspension and an unanswered appeal (see `PLAYBOOK_GOOGLE_ADS.md`, marked
  dead), and **LinkedIn ads were never started.** Actual lifetime paid spend is ~$4, from an
  accidental Google auto-created campaign. The only paid playbook still theoretically open is
  `PLAYBOOK_REDDIT_ADS.md`, which is unstarted and has no pixel installed. Restarting paid
  acquisition is a founder decision, not a scheduled Phase 2 task.
- **Outbound:** 3-touch email + 1 LinkedIn sequence per list; 50 contacts/day/SDR
- **Content:** 2 blog posts/week — teardown style ("What a $2,000/mo MES actually does vs. our $249 bundle")
- **Product Hunt launch** for OPSIQ (manufacturing suite launch copy is already drafted in MARKETING.md)
- **Partnerships:** 5 outreach conversations to industry newsletters (Modern Machine Shop, Manufacturing.net) for sponsored primers

### Phase 3 — Weeks 9–12: Optimize & expand
- Shut down the two worst-performing channels; double budget on the top two
- Launch lifecycle sequences: trial day 1/3/7/14, paid month 1/3, expansion prompts at month 3 into bundle
- Churn-save: automated exit survey + founder reply on any cancel in first 90 days

---

## 6. Sales Motion

**Pure self-serve, video-led.** No live demos, no booking calls. The funnel is:

1. **Education** — visitor lands on storefront or vertical page, watches the per-app YouTube video embedded on the product card
2. **Conversion** — clicks Subscribe, completes Stripe checkout
3. **Activation** — onboarding email sequence (`PLAYBOOK_LIFECYCLE.md` L3) drives first key action
4. **Expansion** — month-3 sequence (L5) prompts bundle upgrade

**No demo-led tier.** Every product, regardless of price, sells through video + storefront + Stripe. Bundle deals ($249+/mo) follow the same path; the bundle CTA is just a different button.

**Human fallback (low priority):** support@plainspokenfoundrynine.com for buyers with questions the video and FAQ don't answer. Not a sales channel — answer once, link to the video, close the loop. SLA: 1 business day.

**Why this works for PF9:**
- Apps are simple enough that a 90-second video shows value clearly
- Pricing is published — nothing to negotiate
- Removes the inbox-triage tax of demo requests
- Lets one founder/operator support the full SKU range without a sales team

---

## 7. KPIs & Reporting

Cowork reports these weekly, same format every time:

| Metric | 30-day target | 90-day target |
|---|---|---|
| Storefront unique visitors | 2,500 | 8,000 |
| Video plays (any product) | 400 | 1,800 |
| Video → Subscribe conversion | 4% | 6% |
| Subscribe modal opens | 200 | 800 |
| Paid conversions | 10 | 60 |
| New MRR | $1,500 | $9,000 |
| CAC (blended) | <$400 | <$300 |

Weekly report format: one page, traffic → video plays → subscribe modal → paid → MRR, with the one thing that changed and the one thing being tested next week.

---

## 8. Budget Envelope (for Cowork to size against)

**Corrected 2026-08-02.** The figures below were an aspirational envelope written at planning
time and were never funded. They are kept only so the delta is visible.

| Line | As originally planned | Actual |
|---|---|---|
| Paid media | $5k/mo starting, scale with CAC | **$0/mo — no live paid channel.** Google Ads cancelled 2026-08-02; LinkedIn ads never started. Lifetime paid spend ~$4 (accidental auto-created campaign, 2026-06-20). The most that was ever authorized was a **$300–500/mo test** ($15/day, property vertical only) — an order of magnitude below $5k/mo, and it never launched. |
| Tooling | under $500/mo | Klaviyo + HubSpot Free + Stripe. Not separately budgeted. |
| Cowork fee | TBD in SOW | See `SOW_COWORK.md` |
| Content production | 2 posts/week, 1 case study / 6 weeks | Not running |

**The $30k first-90-day ceiling is not a real number and should not be quoted.** It was
derived from the $5k/mo paid line above, which no longer exists. Any future paid spend starts
from zero and needs an explicit founder decision on channel and amount.

---

## 9. Deliverables Checklist

Cowork hands back at end of 90 days:
- [ ] CRM populated with full pipeline and disposition history
- [ ] All ad accounts, analytics, and CRM transferred to PF9 ownership
- [ ] Playbooks: outbound sequences, demo script, objection handling, pricing FAQ
- [ ] 12 weekly reports + final readout deck
- [ ] Documented top-2 channels with CAC and conversion benchmarks
- [ ] Roadmap recommendation for months 4–6

---

## 10. Risks & What We Won't Do

- **Don't chase enterprise logos** — it breaks the pricing promise
- **Don't discount below list** — the $249 bundle is already the discount
- **Don't promise integrations we don't have** — keep claims to what's on the storefront today
- **If a channel isn't producing by week 6, kill it** — no sunk-cost extensions

---

**Point of contact:** PF9 founder (single approver for copy, pricing, and spend above envelope).
**Kickoff prerequisite:** access to Stripe dashboard (read-only), storefront analytics, existing MARKETING.md, and founder for 2× 30-minute ICP interviews in week 1.
