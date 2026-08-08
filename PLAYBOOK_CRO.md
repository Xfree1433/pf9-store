# Storefront A/B Test Backlog

**Target page:** https://store.plainspokenfoundrynine.com (`index.html`)
**Tool:** Google Optimize alternative (GrowthBook, VWO, or Optimizely) — confirm during week 1 analytics audit.
**Primary success metric:** demo click rate (storefront → any `*.plainspokenfoundrynine.com/demo` link).
**Secondary metric:** checkout-start rate (any "Subscribe" click).
**Statistical discipline:** minimum 95% confidence, minimum 1,000 visitors per variant, minimum 7-day run (captures weekly pattern). Kill a test at day 14 if it hasn't reached significance — the effect is too small to matter.

---

## Current baseline (as of branch date)

| Element | Current copy |
|---|---|
| Hero headline | "Software that works as hard as you do" |
| Hero subhead | "Practical tools for manufacturing, property management, and operations teams. Deploy in minutes, not months." |
| Primary CTA | "Browse Products" |
| Secondary CTA | "Talk to Us" |
| Trust indicators | "No per-user fees," "Live demos, no signup," "From $49/mo" |
| App CTA pair | "Try Demo" (gray outline) + "Subscribe" (solid) |
| Social proof | None — only a stats block |
| Risk reversal on page | Weak — the 30-day free trial is in the hero, but the CTA area leans on the footer-only 14-day refund line |
| FAQ | None on homepage |

---

## Test prioritization (ICE: Impact × Confidence × Ease, each 1–10)

| # | Test | I | C | E | Score | Order |
|---|---|---|---|---|---|---|
| T1 | Hero headline vertical-specific | 9 | 8 | 9 | 648 | 1 |
| T2 | Elevate "Try Demo" to primary style | 8 | 9 | 10 | 720 | **Ship first** |
| T3 | Add hero risk-reversal line | 7 | 8 | 10 | 560 | 2 |
| T4 | Add testimonial strip above fold | 9 | 6 | 5 | 270 | gate on content |
| T5 | Pricing page simplification | 8 | 7 | 6 | 336 | 3 |
| T6 | Bundle callout in hero | 7 | 7 | 8 | 392 | 4 |
| T7 | Homepage FAQ accordion | 6 | 7 | 7 | 294 | 5 |
| T8 | Exit-intent modal (demo-link capture) | 6 | 6 | 7 | 252 | 6 |
| T9 | Vertical landing pages | 9 | 8 | 3 | 216 | phase 2 |
| T10 | Calculator: "what your current tools cost" | 8 | 5 | 3 | 120 | phase 3 |

Ship tests in the **Order** column, not ICE-raw order — dependencies matter.

---

## T2 — Primary-style "Watch Demo" button (✅ shipped 2026-05-06)

**Status:** Shipped to production on 13 of the 15 Watch Demo cards. Carve-outs:
- **MARKUPR** (waitlist) — Watch Demo stays outline; Join Waitlist (amber) is the only real conversion.
- **COMPLI** (freemium) — Watch Demo stays outline; Start Free is the primary conversion.

**Hypothesis:** "Watch Demo" is the zero-risk entry point, but it reads as secondary next to the solid "Subscribe" button. Making it the visually dominant action raises video-play rate, which is the top-of-funnel leading indicator for paid conversion.

**Variant shipped:** Watch Demo solid black, Subscribe outlined. (No A/B split — shipped as a permanent change since the funnel is video-led; treating this as a baseline shift rather than a test.)

**Watch these metrics for 14 days post-ship:**
- `video_play` rate on app cards — expect significant lift
- `subscribe_modal_open` rate — guardrail, must not drop >15%
- `checkout_started` and Stripe paid-conversion rate — ultimate guardrail

**If guardrail breaches:** revert by swapping the class strings back. The change is reversible in two `replace_all` operations.

---

## T1 — Vertical-specific hero headline

**Hypothesis:** "Software that works as hard as you do" is an identity statement, not a value proposition. Manufacturing buyers (60% of target) respond more strongly to the concrete pain-and-price formulation already proven in `MARKETING.md`.

**Variants:**
- A (control): "Software that works as hard as you do"
- B: "5 practical apps for manufacturers — from $49/mo"
- C: "Flat-rate shop floor software. No per-user fees. Deploy in a week."

**Metric:** scroll-past-hero rate + demo-click rate.
**Guardrail:** property-segment bounce rate.
**Run time:** 14 days, three-way split.
**Note:** if B or C wins, the property and compliance verticals need their own landing pages (see T9) — don't leave them orphaned under a manufacturing hero.

---

## T3 — Hero risk-reversal line

**Hypothesis:** the 30-day free trial is the strongest trust signal PF9 has and it is under-used near the CTA. Surfacing it there reduces purchase anxiety.

**Variant:** add beneath the trust-indicator row: *"30-day free trial. Cancel any time before day 30 and you're not charged."*

> ⚠️ **This test used to propose surfacing "14-day money-back guarantee" instead.** That is the
> weaker and less accurate of the two claims: the 14 days is the refund window on the *first
> charge*, which only ever happens on day 30. Testing the refund policy as the risk-reversal line
> would have measured the wrong lever — nobody is anxious about a refund when they haven't paid
> yet. Test the trial.
**Metric:** Subscribe-click rate.
**Guardrail:** refund request rate (must not spike).
**Run time:** 14 days.

---

## T4 — Testimonial strip above fold

**Hypothesis:** zero social proof is the single largest credibility gap on the storefront. Even 2–3 real quotes outperform none.

**Blocker:** need 3 usable customer quotes before shipping. Cowork week-4 deliverable: collect 5, ship 3.
**Variant:** add a 3-card strip (quote, name, title, company) directly under hero CTAs.
**Metric:** demo-click + Subscribe-click.
**Guardrail:** none.
**Run time:** 21 days.

---

## T5 — Pricing section simplification

**Hypothesis:** the current pricing area shows both per-app cards *and* a separate three-tier block ($49 / $119 / Custom). Two pricing frames compete with each other and the three-tier block doesn't match the app catalog. Removing it raises downstream Subscribe clicks.

**Variants:**
- A (control): both frames shown
- B: remove three-tier block entirely; keep only app cards + the Property Suite bundle callout

**Metric:** Subscribe-click rate.
**Guardrail:** time-on-page (should not drop sharply — if it does, visitors are leaving confused).
**Run time:** 14 days.

---

## T6 — Entry-price callout in hero

> ⚠️ **Rewritten 2026-08-08.** This test used to hoist a "$249/mo bundle — save $86/mo" pill into
> the hero. **That bundle was never purchasable and has been dropped**, so the original variant
> would have tested a claim that 400s at checkout. What's left is the genuinely sharp number:
> the *entry* price. Do not resurrect the savings pill unless a discounted bundle actually exists
> in Stripe.

**Hypothesis:** the hero leads with the platform, not the price. The sharpest true claim PF9 has is that a shop can start for **$49/mo, unlimited users**, against competitors quoting $2,000+/mo. Surfacing entry price in the hero should lift Subscribe starts.

**Variant:** add a pill under the hero CTAs: *"Flat-rate from $49/mo — unlimited users, 30-day free trial"*
**Metric:** Subscribe events started (any product).
**Guardrail:** average order value (must not drop >20% — the risk is anchoring everyone on the cheapest app).
**Run time:** 14 days.

---

## T7 — Homepage FAQ

**Hypothesis:** repeat objections Cowork hears on demos (integrations, security, cancellation, per-user pricing proof) cost conversion on the page too. An accordion block resolves them pre-demo.

**FAQ items to ship (from demo objection log):**
1. Do you charge per user? (No, flat monthly.)
2. How long does setup take? (Minutes to days.)
3. Can I cancel anytime? (Yes — cancel before day 30 and you're never charged; after that it's month-to-month, with a 14-day refund window on the first charge.)
4. Do the apps integrate with [ERP]? (CSV today, roadmap varies — link to contact.)
5. Is my data secure? (Short summary + contact link.)
6. Can I try before I subscribe? (Yes, live demo, no signup.)

**Variant:** accordion block above footer.
**Metric:** Subscribe-click rate + reduction in "is it secure / how long / integrations" inbound questions.
**Run time:** 21 days.

---

## T8 — Exit-intent modal

**Hypothesis:** visitors who bounce without clicking a demo are the easiest segment to convert later. Capture an email for the MARKETING.md drip.

**Variant:** on exit-intent (desktop only), show: *"Before you go — try any app live, no signup: {{button: Pick an app}}. Or get a 2-minute tour by email: {{email capture}}."*
**Metric:** email captures per 1,000 exits.
**Guardrail:** bounce rate (this is already on exit, so should only go up if the modal itself is disruptive).
**Run time:** 21 days.
**Do not ship on mobile.**

---

## T9 — Vertical landing pages (phase 2)

Once T1 proves a vertical-specific hero wins, build three dedicated pages:
- `/manufacturing` — hero + 5 apps + bundle
- `/property` — hero + 4 apps + suite
- `/compliance` — hero + COMPLI free tier

Route paid traffic to the vertical page, not the homepage. Expected lift: 2–3× on paid-traffic conversion based on generic SaaS benchmarks. Gate on: a copywriter week and design review.

---

## T10 — Cost calculator (phase 3)

**Hypothesis:** buyers who calculate their current per-seat software spend commit faster.
**Widget:** "How many users do you have? × $50/user/mo ≈ $X/mo. PF9 flat: $335/mo. You save $X/year."
**Risk:** complex to build well; commit only if T1 + T6 confirm that the price-savings message is the winning angle.

---

## Test hygiene rules

- One test per page section at a time. No overlapping tests on the hero.
- Never test during a paid-traffic spike (launch week) — wait for steady state.
- Always set a guardrail metric. If it breaches, roll back even if the primary metric wins.
- Document every test in this file: hypothesis, dates, variants, result, decision. Include losing tests — they're evidence too.
- No "feels better" ship decisions. If it didn't beat significance, revert to control.

---

## Reporting

Add to the weekly report (per `SALES_PLAN.md` §7):
- Test currently running
- Day-of-test + current lift/loss
- Next test teed up
- Cumulative conversion-rate change since test program started
