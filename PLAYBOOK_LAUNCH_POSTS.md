# PF9 Launch Posts Playbook

Three paste-ready founder posts for big-spike publishing on Hacker News, Twitter/X, and Indie Hackers. Each one is a one-shot — best fired when you have a clean weekday morning to monitor replies for 4–6 hours.

**Why these three:** they reach the same founder/indie audience overlap (engineers, founders, makers, technical buyers). Spread them across 3 separate days, not the same day. If one channel blows up, double down; if all flop, you've still planted three durable backlinks.

**Common framing:** "operators building for operators, tired of per-seat pricing, here's the math." Honest, technical, no hype.

---

## Section A — Hacker News "Show HN"

### When to post

- **Day of week:** Tuesday or Wednesday
- **Time:** 8–9am Pacific (peak HN traffic + best chance of front-page rotation)
- **Don't post:** Mondays (low engagement), Fridays (weekend drop-off), holidays

### Title

```
Show HN: PF9 – Flat-rate manufacturing and property software ($249 / $119 a month)
```

(HN title rules: no clickbait, no marketing language, "Show HN" prefix required for self-launches, ~80 char limit. This title fits.)

### Body

```
Hi HN — I built Plainspoken Foundry Nine because most operational software in manufacturing and property management uses per-user or per-unit pricing that grows linearly with team size or portfolio size.

Two suites:

- Manufacturing Suite ($249/month flat): 5 apps for shop-floor operations — shift handoffs, inventory + WIP, quality (NCR/CAPA, SPC), operational dashboards, mobile field inspections. Unlimited users.

- Property Suite ($119/month flat): property management (leases, rent ledger, maintenance, vendor invoices) + tenant portal (online rent, maintenance requests, lease access). Unlimited units, unlimited tenants.

The pricing math vs the alternatives:

- MRPeasy at 25 users: $1,225/mo (linear $49/user). PF9: $249/mo.
- Buildium at 100 units: ~$167/mo (per-unit fees stack). PF9: $119/mo.
- Enterprise MES quotes: $500/user/mo + $30–80k year-one implementation. PF9: deploy in days.

Six head-to-head comparison pages with honest "where they win" sections at store.plainspokenfoundrynine.com/comparisons/ — Buildium, AppFolio, DoorLoop, MRPeasy, Katana, Fishbowl. The "where they win" sections name real competitor strengths (Buildium's mature accounting, Katana's Shopify-Xero sync, Fishbowl's QuickBooks bidirectional). Pretending otherwise just makes comparison content untrustworthy.

Stack: static HTML + Tailwind front-end (GitHub Pages), Flask + SQLite back-end (Stripe webhooks, Resend email, HubSpot CRM push), 14 product demo videos on YouTube. Each app runs as its own subdomain microservice.

Free interactive cost calculators (per-door for property, per-user for manufacturing). Free downloadable templates (shift handoff, NCR/CAPA log, property inspection checklist) at /lead-magnets/.

Funnel is fully self-serve: no live demos, no sales calls, no "book a meeting." YouTube video → Stripe checkout. 14-day money-back guarantee, cancel anytime.

Looking for honest feedback — especially from anyone running small manufacturing operations (20–250 employees) or small landlord portfolios (5–50 units). What's missing? What would make you switch?

Storefront: https://store.plainspokenfoundrynine.com
Comparisons: https://store.plainspokenfoundrynine.com/comparisons/
Manufacturing landing: https://store.plainspokenfoundrynine.com/for-manufacturers.html
Property landing: https://store.plainspokenfoundrynine.com/for-landlords.html
YouTube channel (14 demos): https://www.youtube.com/@plainspokenfoundrynine
```

### First-hour comment templates

HN comments are often pointed. Have these reply-templates ready (don't paste verbatim — adapt to the actual comment):

**Q: "How is this different from {Buildium / Katana / etc.}?"**
> Mostly flat pricing — those vendors do real things we don't (Buildium's mature accounting, Katana's Shopify sync). The comparison pages cover the trade-offs explicitly. Honest answer is we're the right pick if (a) you have 6+ users / 30+ units and per-seat math hurts, and (b) you don't need the deep features the established vendors built over 10+ years.

**Q: "Why no free tier?"**
> 14-day money-back acts as a free trial without us building separate gated feature paths. The flat $119/$249/mo is intentionally low enough that "subscribe, try, refund if it's not the fit" is the simplest path for both sides.

**Q: "Where's the moat?"**
> Honestly, pricing model + speed-to-deploy. Established vendors can't switch to flat without cannibalizing their core revenue. Speed is easier to copy, but we've already shipped the structural work — the per-seat vendors are years deep in their architecture.

**Q: "What about {feature X} that {Vendor Y} has?"**
> Don't have it today. The comparison page for that vendor names it explicitly under "what they do well." Genuine answer: if X is core to your operation, we're not the fit.

**Q: "How many customers do you have?"**
> Honest answer based on your actual situation. Don't lie. If pre-launch or low-revenue, say so — HN respects honesty more than fake numbers.

**Q: "Why both manufacturing AND property? Aren't those different markets?"**
> They are. The underlying pattern is the same — small-to-mid operators getting nickel-and-dimed by per-X pricing. We started with both because the platform infrastructure (auth, billing, CRM, video pipeline) is shared. The products themselves are specialized.

**Q: "Self-hosted? Open source?"**
> Closed-source SaaS today. Not philosophically opposed to open-sourcing pieces eventually but not in the near-term plan.

### What to do during the post

1. **First 2 hours:** reply to every comment, even one-liners. HN's algorithm weighs response density.
2. **Hours 2–6:** keep monitoring, post substantive replies, ask follow-up questions to keep threads alive.
3. **Don't:** vote-manipulate, ask friends to upvote, post duplicate content elsewhere within 24 hours.
4. **If it dies (no front page within 90 min):** that's the outcome. Don't repost.
5. **If it hits front page:** prep for hundreds of comments. The storefront will see a meaningful traffic spike — watch GA4 Realtime and HubSpot for captures.

---

## Section B — Twitter / X founder thread

### Thread structure (12 tweets)

Each tweet is its own line below. Number them in your client (1/12, 2/12, etc.) or use X's threading.

```
1/12 I shipped 14 product demo videos in two weeks for Plainspoken Foundry Nine — flat-rate manufacturing and property software. No per-seat fees, no per-door fees, no $50k ERP quotes. Here's what I learned and the math against per-seat competitors.

2/12 The pricing model came first. Manufacturing Suite is $249/mo flat for 5 apps. Property Suite is $119/mo flat for the bundle. Unlimited users. The price doesn't change whether you have 5 employees or 250, 5 units or 250.

3/12 The math vs MRPeasy at 25 users: they bill $49 per user per month → $1,225/mo. PF9 stays at $249. Crossover is around 5–6 users. Above that, flat-rate saves real money every month.

4/12 Same against Buildium for landlords. At 50 units, Buildium runs about $92/mo (base + per-unit fees). At 250 units it's about $392. PF9 stays at $119 the whole way.

5/12 The funnel decision: no live demos. No "book a meeting." 14 product videos on YouTube, 90 seconds each. Visitor watches, clicks Subscribe, completes Stripe checkout. End to end self-serve.

6/12 The why: live demos gate purchase behind a calendar. They're a tax on the buyer's time and ours. We're flat-rate and cheap enough that the buyer can subscribe, try it for 14 days, refund if it's not the fit. The video does the explaining.

7/12 The "honest" pivot in the comparison content: every comparison page has a "what they do well" section that genuinely names competitor strengths. Buildium's accounting. Katana's Shopify sync. Fishbowl's QuickBooks integration. Pretending otherwise reads as marketing spin.

8/12 The unexpected lift: prospects respond well to honest comparison. Telling them "we're not the right fit if you need X" builds more trust than pretending we're best at everything. Conversions are still being measured, but the qualitative response from early traffic is clearer.

9/12 What I'd change about the rollout: the first version of the storefront still had "Book a Demo" buttons. Pivoted to YouTube-only after the second week. The customer signal is clearer now — visitors who watch are pre-qualified by the video itself.

10/12 What stayed constant: pricing transparency. Every product price published on the storefront. Every comparison page lists competitor pricing with public sources. Every calculator runs the math at the visitor's exact size. No "request a quote."

11/12 Stack: static HTML + Tailwind on the front-end (GitHub Pages), Flask + SQLite + Stripe webhooks on the back-end, HubSpot for CRM, Resend for transactional email, ElevenLabs + Pixa for video production assistance.

12/12 If you're a small-to-mid manufacturer (20–250 employees) or small landlord (5–50 units) and per-seat pricing has been gnawing at your software budget, look at PF9. https://store.plainspokenfoundrynine.com — happy to take questions in replies.
```

### Engagement notes

- **Reply to every meaningful reply within first 4 hours.** Drives X's "reply velocity" signal.
- **Don't post and ghost.** Threads that die in the first hour rarely recover.
- **Quote-tweet your own thread** with a one-line addendum 24 hours later to give it a second life if engagement is meaningful.
- **Use 1–2 hashtags max per tweet**, not 5. `#manufacturing` `#saas` `#flatpricing` work for relevance. More than that signals spam.

### Tweets that work as standalone follow-ups

If the thread doesn't blow up, these can be cherry-picked as standalone tweets in the following week:

```
Most manufacturing software charges per user. At 25 users on MRPeasy that's $1,225/mo. Same software at 50 users? $2,450. Same again at 100? $4,900.

PF9 Manufacturing Suite is $249/mo flat. The price doesn't change when you hire.

https://store.plainspokenfoundrynine.com/for-manufacturers.html
```

```
Buildium starts at $62/mo. AppFolio requires 50 units minimum. DoorLoop's Starter caps at 10 units then jumps to $189.

PF9 Property Suite: $119/mo flat. Any portfolio size. From 1 unit to 500.

Honest comparison pages for each: https://store.plainspokenfoundrynine.com/comparisons/
```

```
Built 14 product demo videos in 2 weeks for our flat-rate SaaS. Each one is 90 seconds. No signup, no sales call.

The funnel: visitor → YouTube → Stripe. End to end self-serve.

Channel: https://www.youtube.com/@plainspokenfoundrynine
```

---

## Section C — Indie Hackers post

### When to post

Indie Hackers is timezone-agnostic — engagement spans 24 hours globally. Post when you can reply for the first 4 hours. Tuesday-Thursday gets the most traction.

### Title

```
I built a flat-rate alternative to per-seat manufacturing and property software ($249 / $119 / mo). Looking for honest feedback.
```

### Body

```
Background: I run a small manufacturing operation and watched every software vendor charge per user or per unit. Buildium, AppFolio, DoorLoop in property. MRPeasy, Katana, Fishbowl in manufacturing. Plus the enterprise tier — Plex, NetSuite, Epicor — that quotes $500/user/mo plus a 6-month implementation.

So I built PF9. Two suites, both flat-rate:

**Manufacturing Suite — $249/month flat, unlimited users**
Five apps for shop-floor ops:
- SHIFTLOG: digital shift handoffs ($49 standalone)
- FLOWTRACK: inventory + WIP + barcodes ($99)
- QUALIFI: NCR/CAPA quality management ($79)
- REPORTR: drag-and-drop dashboards ($59)
- INSPECTR: mobile field inspections ($49)

**Property Suite — $119/month flat, unlimited units**
- LANDLORDR: property management ($89 standalone)
- TENANTLINK: tenant portal ($49)

**The math vs competitors:**
At 25 users on MRPeasy: $1,225/mo. PF9: $249.
At 50 units on Buildium: ~$92/mo. PF9: $119.
At 100 units on Buildium: ~$167. PF9: still $119.

**Funnel decisions worth discussing:**

1. No live demos. 14 product videos on YouTube (90 seconds each). Buyer watches, clicks Subscribe, completes Stripe checkout. Pure self-serve.

2. Honest comparison pages. Each one has a "what they do well" section that names real competitor strengths. Buildium's mature accounting. Katana's Shopify-Xero sync. We say what they win on.

3. 14-day money-back, no contracts, no per-X fees ever. Cancel anytime.

**Stack (for the technically curious):**
- Static HTML + Tailwind storefront (GitHub Pages)
- Flask + SQLite back-end with Stripe webhooks
- HubSpot for CRM, Resend for email
- ElevenLabs + Pixa for video production
- Each product app runs as its own subdomain microservice

**Free stuff (no signup hoops):**
- Per-user and per-door cost calculators: store.plainspokenfoundrynine.com/tools/per-user-calculator.html
- Printable templates: shift handoff, NCR/CAPA log, property inspection
- Software pricing glossary: MES vs ERP, what is per-door pricing, etc.

**What I'm looking for from this community:**
- Honest feedback on the comparison-page approach (the "what they do well" sections specifically)
- Pricing critique — am I leaving money on the table at $249/$119?
- What's missing that would block you from switching from your current setup?
- Other indie hackers who've shipped product video pipelines at this scale (14 videos in 2 weeks) — how did you maintain quality?

Storefront: https://store.plainspokenfoundrynine.com
Manufacturing landing: store.plainspokenfoundrynine.com/for-manufacturers.html
Property landing: store.plainspokenfoundrynine.com/for-landlords.html
All comparisons: store.plainspokenfoundrynine.com/comparisons/
14 YouTube demos: youtube.com/@plainspokenfoundrynine

Happy to share more on the stack, the pricing model decision, or the no-demo pivot if there's interest.
```

### Indie Hackers engagement rules

- **Reply to every comment**, even ones that disagree
- **Engage in other IH posts** in the same week — don't just post and ghost
- **Don't link-drop in unrelated threads.** Be a contributor, not a promoter.

---

## Section D — Scheduling and sequencing

Don't post all three on the same day. Spread them:

| Day | Channel | Time | Why |
|---|---|---|---|
| Tuesday | Hacker News Show HN | 8am PT | Peak HN traffic |
| Wednesday | Twitter/X thread | 9am ET | Morning attention window for B2B Twitter |
| Thursday | Indie Hackers | 7am ET | Morning newsletter cycle |

If HN blows up Tuesday, **delay Wednesday's Twitter thread** to ride the HN wave with a "as some of you saw on HN..." follow-up. If HN dies, post Twitter as planned.

---

## Section E — Tracking

Add these to your GA4 → Acquisition → Traffic acquisition view as referrers to monitor post-launch:

- `news.ycombinator.com` — HN traffic
- `t.co` / `x.com` — Twitter
- `indiehackers.com` — Indie Hackers

Set a 7-day reminder after each post to check:
- Traffic volume from that referrer
- Email captures (modal + lead magnets) attributed to that source
- Stripe paid conversions (any?)

Document the outcome in `memory.md` so future PR descriptions know what worked.

---

## What I (the agent) can help with after launch

- Write follow-up tweets if the thread blows up
- Draft response templates for repeated HN questions you hit
- Update the storefront copy if the launch reveals a positioning weakness
- Iterate on the comparison pages if specific competitor questions keep coming up

## What I cannot do

- Post on your behalf (your accounts, your reputation)
- Predict whether HN will pick it up (algorithm + audience luck)
- Vote-manipulate or run gray-hat amplification — and you shouldn't either
