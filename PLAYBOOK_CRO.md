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
| Risk reversal on page | None — 14-day money-back is footer-only |
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

## T2 — Primary-style "Try Demo" button (ship first)

**Hypothesis:** "Try Demo" is the zero-risk entry point, but it reads as secondary next to the solid "Subscribe" button. Making it the visually dominant action raises demo-click rate, which is the top-of-funnel leading indicator for paid conversion.

**Variant:**
- A (control): "Try Demo" gray outline + "Subscribe" solid
- B: "Try Demo" solid primary + "Subscribe" outline

**Metric:** demo-click rate on app cards.
**Guardrail:** Subscribe-click rate (must not drop >15%).
**Run time:** 14 days.
**Why ship first:** single CSS change, highest confidence, clears the measurement baseline for everything else.

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

**Hypothesis:** the 14-day money-back guarantee is a real trust signal that's buried in the footer. Surfacing it near the CTA reduces purchase anxiety.

**Variant:** add beneath the trust-indicator row: *"14-day money-back guarantee. Cancel anytime."*
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

## T6 — Bundle callout in hero

**Hypothesis:** the $249/mo five-app bundle is the sharpest value claim PF9 has ("competitors charge $2,000+/mo"). It's hidden deep in the page. Hoisting it into the hero drives bundle-share of revenue.

**Variant:** add a pill under the hero CTAs: *"Or bundle all 5 manufacturing apps for $249/mo — save $86/mo"*
**Metric:** clicks on the bundle link + bundle-share of Subscribe events.
**Guardrail:** single-app Subscribe rate (must not drop >20%).
**Run time:** 14 days.

---

## T7 — Homepage FAQ

**Hypothesis:** repeat objections Cowork hears on demos (integrations, security, cancellation, per-user pricing proof) cost conversion on the page too. An accordion block resolves them pre-demo.

**FAQ items to ship (from demo objection log):**
1. Do you charge per user? (No, flat monthly.)
2. How long does setup take? (Minutes to days.)
3. Can I cancel anytime? (Yes, 14-day money-back, then month-to-month.)
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
**Widget:** "How many users do you have? × $50/user/mo ≈ $X/mo. PF9 flat: $249/mo. You save $X/year."
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
