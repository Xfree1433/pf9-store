# HN Launch Day — One-Screen Kit

> # ✅ BLOCKER CLEARED 2026-08-08 — the $249 bundle was dropped
>
> This post used to lead with a **$249 Manufacturing Suite that could not be bought.** There was no
> `MANUFACTURING_BUNDLE` in `store_api.py`'s `PRICE_MAP`, and checkout rejects anything not in that
> map (`400 Unknown product`), so the headline offer had no checkout at all — and it advertised a
> price **$86/mo cheaper than the only price a customer could actually pay.**
>
> **Founder decision was to drop the bundle, not to create the Stripe price.** Every `$249` claim has
> been stripped from the site, the JSON-LD, and the copy bank. The numbers below are the real ones:
>
> - **$49/mo** — entry price, one app, unlimited users. Purchasable today.
> - **$335/mo** — all five manufacturing apps, subscribed individually. **No discount**; $335 is
>   exactly `$99 + $79 + $49 + $59 + $49`.
> - **$119/mo Property Suite is the only real bundle** (`PROPERTY_BUNDLE`, vs $138 standalone).
>   Never write "bundles" plural.
>
> ⚠️ The crossover point moved with the price: PF9 now beats MRPeasy above **~7 users** (was 5–6).
> Fishbowl stays ~6 and Katana ~3 — their tier structures absorbed the change.
> The title and body below have been rewritten to lead with **$49**, which is both the truer hook and
> the cheaper-sounding one. **This file is now clear to post.**

**This is the only file you need open on launch morning.** Everything is copy-paste ready and in order. Work top to bottom.

**When:** the next **Tuesday** (or Wednesday), **8:00–9:00am Pacific** = 11am–12pm Eastern. Not Mon, not Fri, not a holiday.

**Where:** https://news.ycombinator.com/submit (log in first — top-right)

**Time commitment:** post takes 3 min; then stay at the keyboard for **2 hours** to reply to comments. That 2-hour window is the whole game.

---

## ⏱️ Minute-by-minute

| Time | Do this |
|---|---|
| **T-10 min** | Log into HN. Open this file + the storefront in other tabs. Coffee ready. |
| **T-0 (8am PT)** | Submit the post (title + body below). URL field **empty**. |
| **First 5 min** | Copy your post's URL. Keep the tab open. Do NOT upvote your own post. |
| **First 2 hrs** | Reply to **every** comment, even one-liners. Fast replies drive ranking. Use the templates below, adapted. |
| **Hrs 2–6** | Keep replying to substantive comments. Ask follow-up questions to keep threads alive. |
| **~90 min mark** | If it hasn't hit the front page, that's the outcome — don't repost, don't panic. You still got a permanent backlink. |
| **If it takes off** | Watch PostHog Realtime + HubSpot for the traffic wave. Prep for hundreds of comments. |

---

## 1. Title — paste into the "title" field

```
Show HN: PF9 – Flat-rate manufacturing and property software, from $49/month
```

## 2. URL field — LEAVE EMPTY

If you fill the URL field, the text box disappears. You want the text post. Skip URL.

## 3. Body — paste into the "text" field

```
Hi HN — I built Plainspoken Foundry Nine because most operational software in manufacturing and property management uses per-user or per-unit pricing that grows linearly with team size or portfolio size.

Two suites:

- Manufacturing (5 apps, $49–$99/month each, $335 for all five): shift handoffs, inventory + WIP, quality (NCR/CAPA, SPC), operational dashboards, mobile field inspections. Each one is a flat monthly price with unlimited users — take one app or take all five.

- Property Suite ($119/month flat): property management (leases, rent ledger, maintenance, vendor invoices) + tenant portal (online rent, maintenance requests, lease access). Unlimited units, unlimited tenants.

The pricing math vs the alternatives:

- MRPeasy at 25 users: $1,225/mo (linear $49/user). PF9: $335/mo for all five apps, flat. Crossover is around 7 users — below that MRPeasy is cheaper, and I'd rather say so than pretend.
- Buildium at 100 units: ~$167/mo (per-unit fees stack). PF9: $119/mo.
- Enterprise MES quotes: $500/user/mo + $30–80k year-one implementation. PF9: deploy in days.

Six head-to-head comparison pages with honest "where they win" sections at store.plainspokenfoundrynine.com/comparisons/ — Buildium, AppFolio, DoorLoop, MRPeasy, Katana, Fishbowl. The "where they win" sections name real competitor strengths (Buildium's mature accounting, Katana's Shopify-Xero sync, Fishbowl's QuickBooks bidirectional). Pretending otherwise just makes comparison content untrustworthy.

Stack: static HTML + Tailwind front-end (GitHub Pages), Flask + SQLite back-end (Stripe webhooks, Resend email, HubSpot CRM push), 13 product demo videos on YouTube. Each app runs as its own subdomain microservice.

Free interactive cost calculators (per-door for property, per-user for manufacturing). Free downloadable templates (shift handoff, NCR/CAPA log, property inspection checklist) at /lead-magnets/.

Funnel is fully self-serve: no live demos, no sales calls, no "book a meeting." YouTube video → Stripe checkout. Every subscription starts with a 30-day free trial (card up front, first charge on day 30, cancel any time before then); if it does convert and you didn't mean to continue, there's a 14-day refund window on that first charge.

Looking for honest feedback — especially from anyone running small manufacturing operations (20–250 employees) or small landlord portfolios (5–50 units). What's missing? What would make you switch?

Storefront: https://store.plainspokenfoundrynine.com
Comparisons: https://store.plainspokenfoundrynine.com/comparisons/
Manufacturing landing: https://store.plainspokenfoundrynine.com/for-manufacturers.html
Property landing: https://store.plainspokenfoundrynine.com/for-landlords.html
YouTube channel (13 demos): https://www.youtube.com/@plainspokenfoundrynine
```

## 4. Then click **submit**. Copy your post's URL. Keep the tab open.

---

## First-hour reply templates

Keep these here and adapt to the real comment — never paste verbatim. HN can smell canned answers. First person, honest, concede real limits.

**"How is this different from {Buildium / Katana / etc.}?"**
> Mostly flat pricing — those vendors do real things we don't (Buildium's mature accounting, Katana's Shopify sync). The comparison pages cover the trade-offs explicitly. Honest answer is we're the right pick if (a) you have 7+ users / 30+ units and per-seat math hurts, and (b) you don't need the deep features the established vendors built over 10+ years.

**"Why no free tier?"**
> There is a free trial — 30 days, on every subscription. Card up front, first charge on day 30, cancel any time before it. If it does convert and you didn't mean to continue, there's a 14-day refund window on that first charge. What we don't have is a permanently free *tier*, because that means building and maintaining gated feature paths, and at $49–$119 flat the trial does the same job for both sides.

> 🔴 **This answer was WRONG until 2026-08-08 and would have cost you the thread.** It used to read
> "14-day money-back acts as a free trial" — i.e. it denied having a free trial. **PF9 has a 30-day
> free trial**, implemented (`store_api.py:623,1845` — `trial_period_days=30`), documented
> (`refund.html`: "Every new subscription begins with a 30-day free trial"), and advertised in the
> storefront hero. Telling HN "no free tier" while your own landing page says **30-Day Free Trial**
> is a one-click catch, on the exact audience that checks. The 14-day figure is real but it is the
> **refund window on the first charge**, not the trial — don't conflate them again.

**"Where's the moat?"**
> Honestly, pricing model + speed-to-deploy. Established vendors can't switch to flat without cannibalizing their core revenue. Speed is easier to copy, but we've already shipped the structural work — the per-seat vendors are years deep in their architecture.

**"What about {feature X} that {Vendor Y} has?"**
> Don't have it today. The comparison page for that vendor names it explicitly under "what they do well." Genuine answer: if X is core to your operation, we're not the fit.

**"How many customers do you have?"**
> Answer honestly for your real situation. If pre-launch/low-revenue, say so. HN respects honesty over fake numbers — do NOT invent traction.

**"Why both manufacturing AND property? Aren't those different markets?"**
> They are. The underlying pattern is the same — small-to-mid operators getting nickel-and-dimed by per-X pricing. We started with both because the platform infrastructure (auth, billing, CRM, video pipeline) is shared. The products themselves are specialized.

**"Self-hosted? Open source?"**
> Closed-source SaaS today. Not philosophically opposed to open-sourcing pieces eventually, but not in the near-term plan.

---

## The rules that get posts killed (don't break these)

- ❌ **Do NOT ask anyone to upvote.** Not friends, not family, not a second account. HN detects vote rings and will bury or ban the post.
- ❌ **Do NOT upvote your own post** from another account.
- ❌ **Do NOT repost** if it flops. One shot per launch.
- ❌ **Do NOT post the same content to Twitter/IH within 24h** — space them out (Wed/Thu).
- ✅ **DO reply fast and honestly.** Response density + good-faith answers are what push a Show HN up.

---

## After the post (same week)

- **Wed** — Twitter/X thread (`PLAYBOOK_LAUNCH_POSTS.md` §B). If HN took off, delay and ride the wave with an "as some of you saw on HN…" angle.
- **Thu** — Indie Hackers (`PLAYBOOK_LAUNCH_POSTS.md` §C).
- **Track it:** PostHog Realtime for the live wave; add `news.ycombinator.com` as a referrer to watch. Note the outcome (peak visitors, any leads/sales) in `memory.md`.

---

## The one-line pep talk

Your funnel already holds attention (3m26s avg session, 32.7% bounce on the trickle of traffic you have). The only thing missing is people. This post is how you get them, it's free, and it's written. Open the tab. Paste. Post. Reply for two hours. That's the whole job.
