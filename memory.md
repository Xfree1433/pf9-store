# PF9 Project Memory

**Purpose:** durable session state so any future agent (me, another Claude session, or a human) can pick up without re-deriving context.

**Last updated:** 2026-05-08
**Active session:** https://claude.ai/code/session_01PDCcag8KXiq7YURGhjqPrn

---

## Project at a glance

**Plainspoken Foundry Nine (PF9)** — multi-vertical SaaS app store. 14 shipped products + waitlists. Founder: **Kennedy Pierce**. Site: https://store.plainspokenfoundrynine.com.

**Core differentiator:** flat monthly pricing, no per-user/per-unit fees. Buyers compare against per-seat MES quotes ($500+/user/mo) and per-door property software (Buildium, AppFolio).

**Funnel model (decided 2026-05):** pure self-serve, **video-led**. No live demos. No booking calls. Path: visitor → YouTube product video → Stripe checkout. Support email kept as low-priority fallback only.

---

## Current state — what's live and working

### Storefront (`store.plainspokenfoundrynine.com`)
- **14 product cards** linking to specific YouTube videos
- **2 vertical landing pages:** `/for-landlords.html`, `/for-manufacturers.html`
- **2 cost calculators:** `/tools/per-door-calculator.html`, `/tools/per-user-calculator.html`
- **6 competitor comparison pages** at `/comparisons/` (Buildium, AppFolio, DoorLoop, MRPeasy, Katana, Fishbowl vs PF9 — plus a hub index)
- **Stripe checkout** wired and live
- **GA4 events** firing and **confirmed reaching GA4 Realtime** (2026-05-08): `video_play`, `subscribe_modal_open`, `checkout_started`, `support_email_click`, `waitlist_open`, `waitlist_submit`. All 8 custom dimensions registered (`product`, `price`, `source_page`, `destination`, `subject`, `calculator`, `units`, `users`). `video_play` marked as Key Event; remaining 4 events pending GA4 Admin refresh (2–4 hour delay before they're markable).
- **JSON-LD schema** on every page: Product, FAQPage, BreadcrumbList, VideoObject (14 entries on index)
- **CRO Test T2 shipped:** Watch Demo is solid black primary, Subscribe is outline secondary, on 13 of 15 cards (carve-outs: MARKUPR waitlist, COMPLI freemium)
- **Email capture modal** (`assets/email-capture.js`) on 10 conversion surfaces (index, 2 vertical landings, 1 comparisons hub, 6 comparison pages). Desktop exit-intent + mobile 60% scroll trigger, 8-second minimum time on page, 7-day dismissal cooldown, once-per-session via sessionStorage. Captures land in HubSpot with `product='STOREFRONT (email capture)'` (no list assignment by default — add `HUBSPOT_LIST_NEWSLETTER` env var if you want them auto-listed).

### Backend (`store_api.py` on 139.94.250.128)
- Flask app with Stripe webhooks for `checkout.session.completed`, `customer.subscription.deleted`, `customer.subscription.updated`, `invoice.payment_failed`
- SQLite tables: `subscriptions`, `demo_requests`
- Resend for transactional email (welcome on subscribe)
- **No CRM integration yet** (waiting on user to pick HubSpot/Loops/etc.)

### Strategy & playbook docs
| File | Purpose |
|---|---|
| `SALES_PLAN.md` | 90-day strategy, ICPs, KPIs, video-led funnel |
| `MARKETING.md` | Pre-existing copy bank — Product Hunt, LinkedIn drip, email templates |
| `SOW_COWORK.md` | Commercial terms for human agency engagement (largely N/A for agent deployment) |
| `PLAYBOOK_OUTBOUND.md` | 14-day SDR sequence (video-led CTAs, no demos) |
| `PLAYBOOK_LIFECYCLE.md` | 7 email sequences (L1 video-viewer, L2 cart-abandon, L3 onboarding, L4 testimonial, L5 expansion, L6 churn-save, L7 win-back) |
| `PLAYBOOK_CRO.md` | A/B test backlog. T2 marked shipped; T1, T3–T10 still pending |
| `PLAYBOOK_VIDEOS.md` | Per-app video scripts + status table (14/14 live + 1 OPSIQ waitlist + 1 MARKUPR waitlist) |
| `PLAYBOOK_GOOGLE_ADS.md` | Paid-search playbook: campaign architecture, keywords, ad copy, conversion tracking, bidding, kill criteria |
| `tools/google-ads/` | Pre-built Google Ads Editor import CSVs (campaigns, ad groups, keywords, ads, negatives) + README. Saves ~2h of manual clicking when launching paid. Campaigns import as Paused with $0 budget — explicit step required to enable. |
| `PLAYBOOK_YOUTUBE.md` | YouTube channel SEO playbook: channel description, banner specs, 5 playlists with binge-watch order, per-video metadata templates (titles, tags, chapters, end screens), pinned-comment template, maintenance cadence. ~45 min total to paste everything into YouTube Studio. |
| `PLAYBOOK_DIRECTORIES.md` | Free SaaS / startup directory submission list with per-directory notes: 15+ directories across general SaaS (AlternativeTo, SaaSHub, Crunchbase, BetaList), vertical-specific (ThomasNet, BiggerPockets), and integration marketplaces (Stripe Partner Directory, QuickBooks App Marketplace). Reusable submission assets at the top. |
| `glossary/` | 6 SEO glossary pages (MES vs ERP, MRP vs ERP, per-door pricing, per-seat pricing, property pricing models, manufacturing pricing models) + hub. Top-of-funnel SEO targets covering education queries; complement the comparison pages' bottom-of-funnel buyer intent. |
| `lead-magnets/` | 3 free-template landing pages (shift handoff, NCR/CAPA log, property inspection) + hub. Email-gated downloads landing in HubSpot with product tag `MANUFACTURING_LEAD_MAGNET (...)` or `PROPERTY_LEAD_MAGNET (...)` — automatic list routing via existing `_hubspot_list_for_product` logic. Different intent segment than calculators (template-seekers vs price-comparers). |
| `templates/` | 3 printable HTML templates served to lead-magnet submitters: shift handoff (1 page), NCR/CAPA log (1 page), property inspection (2 pages). Print-styled CSS, browser-renderable, save-as-PDF friendly. `noindex` meta (gated content). |
| `AGENTS.md` | 5 agent system prompts (Orchestrator, SDR, Growth, Lifecycle, Creative). AE Assist agent dropped — no demos to assist with. |
| `tools/capture_screenshots.py` | Playwright batch screenshot tool |
| `tools/compose_video.py` | ffmpeg + voiceover composition |

### YouTube channel
**URL:** https://www.youtube.com/@plainspokenfoundrynine
**14 videos live**, all linked from storefront product cards:

| Product | Video URL | Price |
|---|---|---|
| FLOWTRACK | https://youtu.be/VA_TKydOxuQ | $99/mo |
| QUALIFI | https://youtu.be/42TdtdcaUnk | $79/mo |
| SHIFTLOG | https://youtu.be/AZA8wj916Sc | $49/mo |
| INSPECTR | https://youtu.be/_1SQDCRjhf0 | $49/mo |
| REPORTR | https://youtu.be/YLrNw3ZMLXc | $59/mo |
| LANDLORDR | https://youtu.be/lpA0qVSOyBY | $89/mo |
| TENANTLINK | https://youtu.be/w_02sqH1n3s | $49/mo |
| PROPERTY_BUNDLE | https://youtu.be/63TRUxSKeho | $119/mo |
| PERMITR | https://youtu.be/RzKqlyjprMM | $299/mo |
| TASKFLOW | https://youtu.be/O2lUhXMeA34 | $69/mo |
| EXTRACTR | https://youtu.be/0rpvA708nFI | $149/mo |
| SUPPORTR | https://youtu.be/jVm4NyP_Ssk | $79/mo |
| MAINTAINR | https://youtu.be/eHUC-CvuQig | $99/mo |
| COMPLI | https://youtu.be/Y-gxxXJ-EkQ | Free tier |

**Waitlist (no video by design):** OPSIQ, MARKUPR

---

## Decisions made (don't re-litigate without reason)

1. **Video-led, not demo-led** (PR #4) — founder explicitly chose YouTube videos over live demos. Anywhere `book a demo` / `walkthrough` language existed, it was replaced with `Watch Demo` → YouTube. Kept support email as fallback only.
2. **Cowork agents, not human agency** — `SOW_COWORK.md` is mostly informational. Real handoff is via `AGENTS.md` system prompts.
3. **HubSpot Free recommended for CRM** — user hasn't picked yet. Loops or Customer.io are acceptable alternatives.
4. **T2 (Watch Demo as primary button) shipped without A/B split** — treated as a permanent change with revert procedure documented in `PLAYBOOK_CRO.md` §T2.
5. **MARKUPR and COMPLI exempt from T2** — waitlist (Join Waitlist amber stays primary) and freemium (Start Free stays primary) cards keep their natural primaries.
6. **AE Assist agent dropped from `AGENTS.md`** — no demos exist to assist with.
7. **Creative agent repositioned as central production agent** (formerly support role). Video is the funnel; Creative produces it.
8. **Cowork rollout order:** Creative + Lifecycle first, then Orchestrator, then SDR, then Growth.

---

## Open items / waiting on user

### Closed since last update
- [x] **PR #13 merged** (6 comparison pages + hub) — 2026-05-08
- [x] **PR #14 merged** (this file added) — 2026-05-08
- [x] **`video_play` confirmed reaching GA4 Realtime** — 2026-05-08. The 503s seen earlier were a local-browser ad-blocker artifact; real visitors land cleanly. Both `video_play` (custom listener) and built-in Enhanced Measurement `click` fire on every Watch Demo click.
- [x] **GA4 custom dimensions registered** — all 8 (Product, Price, Source page, Destination URL, Subject, Calculator, Units, Users). 24–48h before the standard Events report shows breakdowns.
- [x] **`video_play` marked as Key Event** — 2026-05-08. Other 4 (`subscribe_modal_open`, `checkout_started`, `support_email_click`, `waitlist_open`) all triggered and confirmed in Realtime; pending GA4 Admin Events tab refresh (2–4h delay) before they appear and can be ☆-marked.

### Open

#### Blocking nothing but high-leverage
- [ ] **Mark remaining 4 events as Key Events** (~10s click each, after GA4 Admin Events list refreshes 2–4h post-trigger): `subscribe_modal_open`, `checkout_started`, `support_email_click`, `waitlist_open`.
- [ ] **Submit `sitemap.xml` to Google Search Console** — without this, the 6 comparison pages won't get indexed quickly. 10-minute setup. User needs to verify the property first; agent can add the verification meta tag once user pastes it.

### Blocking the Lifecycle agent
- [ ] **Pick a CRM** (HubSpot Free recommended). Once chosen, agent writes a ~30-line integration in `store_api.py` that pushes leads/subscribers from the calculators and Stripe webhooks.

### Blocking real revenue (the actual bottleneck)
- [ ] **Drive traffic.** Site has 3 users / 21 events in last 7 days as of 2026-05-08. Funnel is fully built; nobody's walking in. Channels in `MARKETING.md`:
  - Outbound (`PLAYBOOK_OUTBOUND.md` is ready — needs sender like Apollo/Smartlead)
  - LinkedIn organic drip (already drafted in MARKETING.md)
  - Paid (Google Search + LinkedIn Ads — needs ad accounts and budget)
  - Product Hunt launch (copy ready in MARKETING.md)
  - Reddit/community (templates in MARKETING.md, needs founder judgment)

### After traffic + CRM exists
- [ ] **Set up Cowork Lifecycle agent** per `AGENTS.md` Agent 4. Dry-run for 48 hr in approval queue, then go live with sequence L3 (onboarding) first.
- [ ] **Set up Cowork Orchestrator agent** per `AGENTS.md` Agent 1. Weekly report Friday EOD.
- [ ] **Add SDR + Creative + Growth agents** per `AGENTS.md` rollout order.

### Watch
- [ ] **T2 metrics for 14 days post-deploy** — `video_play` rate should lift; `subscribe_modal_open` and Stripe paid-conversion are guardrails (must not drop >15%). Decision date pushed from 2026-05-21 to ~2026-05-22 due to PR #12 selector bug that silently broke `video_play` for the first 2 days. Revert procedure in `PLAYBOOK_CRO.md` §T2.

---

## Known issues / gotchas

1. **GA4 standard Events report has 24–48h latency** and won't show custom event parameters until the corresponding Custom Dimensions are registered in Admin. The Admin → Events list itself has its own 2–4h refresh delay before newly-fired events show up to be ☆-marked. **Verify firing in DebugView or Realtime, not the standard report.**

2. **Test-browser 503s on `/g/collect`** are likely an ad-blocker / privacy-extension artifact. Real visitors won't have this. Don't chase the 503 unless DebugView from a clean device also fails.

3. **`video_play` selector originally only matched `youtube.com`** — bug was that storefront URLs use the short `youtu.be/...` form. Fixed in PR #12 by extending selector to match both. Any new comparison/landing page must use the same selector pattern: `a[href*="youtube.com"], a[href*="youtu.be"]`.

4. **The contact form `id`s/`name`s are still `demo*`** (e.g., `demoForm`, `demoSubmit`, `demoEmail`) for backend-compat with the `/demo-request` POST handler in `store_api.py`. Visible labels were updated to "Send Question" / pre-sales framing. Don't rename ids without also updating the backend.

5. **The deploy workflow (`.github/workflows/deploy.yml`) targets GitHub Pages on push to main.** Custom domain `store.plainspokenfoundrynine.com` is served from there. Deploys take 1–3 minutes. After merge, allow time for CDN cache plus browser cache before testing — use incognito to bust browser cache.

6. **`PLAYBOOK_VIDEOS.md` `tools/capture_screenshots.py` runs Playwright** — won't work from this Claude session because demo URLs are blocked. User runs it locally from a network with access.

7. **MARKUPR waitlist Watch Demo button uses channel-root href.** When MARKUPR ships, the swap is one line: change href to the new video URL, append a VideoObject entry to JSON-LD on `index.html`, update `PLAYBOOK_VIDEOS.md` status table. Same pattern as PR #6 / #9.

8. **Pricing in comparison pages is dated to May 2026** — vendors change pricing frequently. Footer disclaimer notes this. If MRPeasy/Katana/Buildium/etc. adjust pricing, just update the affected rows.

9. **Trademarks in comparison pages** — every comparison page has a footer disclaimer naming the competitor as their owner's trademark. Don't remove these.

10. ~~**Some sections of `MARKETING.md` reference "Book a 20-min demo"**~~ — refreshed 2026-05-10. `MARKETING.md` now matches the video-led, no-demo storefront: Product Hunt listings for both verticals, 7 LinkedIn posts (5 manufacturing + 2 property), 2 Reddit drafts, 2 outbound email templates, COMPLI section. All demo CTAs replaced with YouTube links. References calculators and comparison pages as proof points.

---

## Important files (where things are)

| Need to... | File |
|---|---|
| Understand strategy | `SALES_PLAN.md` |
| Read founder voice | `for-landlords.html` lines 252–264 (founder note) |
| Look up product/price | `index.html` lines 247–581 (product cards with `openSubscribe` calls) |
| Check video URL for an app | `PLAYBOOK_VIDEOS.md` status table (top of file) |
| Find an analytics event | `index.html` lines ~860–1000 (script section) |
| Update agent prompts | `AGENTS.md` |
| Update outbound copy | `PLAYBOOK_OUTBOUND.md` |
| Add a sitemap entry | `sitemap.xml` |
| Wire a new CRO test | `PLAYBOOK_CRO.md` (test catalog T1–T10) |

---

## Branch / PR conventions

- Branch from main: `claude/pf9-{kebab-task-name}`
- Squash-merge PRs (clean history on main)
- Delete local branch after merge: `git branch -d claude/pf9-...`
- Remote branch deletion is blocked from the sandboxed git proxy — user deletes remote branches via GitHub web UI
- Every PR includes a "Test plan" checklist
- Every PR description references the session URL at the bottom

---

## Recent PR history (most-recent first)

| # | Title | Status |
|---|---|---|
| 14 | Add memory.md — project state for future sessions | Merged 2026-05-08 |
| 13 | Add 6 competitor comparison pages + hub | Merged 2026-05-08 |
| 12 | Fix video_play event selector — match youtu.be URLs too | Merged 2026-05-07 |
| 11 | Add per-user pricing calculator (CRO Test T10) + cleanup | Merged 2026-05-07 |
| 10 | Add for-manufacturers.html — vertical landing page (CRO Test T9) | Merged 2026-05-07 |
| 9 | Wire final 5 video URLs — 14/14 shipped products linked | Merged 2026-05-07 |
| 8 | Ship CRO Test T2: Promote Watch Demo to primary button | Merged 2026-05-07 |
| 7 | Post-video cleanup: stale-demo language, video schema, tracking | Merged 2026-05-07 |
| 6 | Wire per-app YouTube video URLs to Watch Demo buttons | Merged 2026-05-06 |
| 5 | Add per-app video production package (14 scripts + storyboards) | Merged 2026-05-06 |
| 4 | Pivot to video-led self-serve funnel (no demos) | Merged 2026-05-06 |
| 3 | Wire GA4 events on storefront CTAs | Merged 2026-05-06 |
| 2 | Add Creative agent (ElevenLabs + Pixa) | Merged 2026-05-06 |
| 1 | Marketing & sales plan + Cowork handoff kit | Merged 2026-05-05 |

---

## What I (the agent) cannot do

- **Render videos** (no demo URL access from sandbox, no ElevenLabs MCP in this session, no YouTube upload credentials)
- **Run `tools/capture_screenshots.py`** (Playwright + demo URL access required)
- **Set up GA4 admin / GSC** (user account access needed)
- **Sign up for HubSpot / pick a CRM** (user account creation needed)
- **Stand up Cowork agents** (Cowork UI access needed)
- **Drive paid ads / outbound** (ad account + sender + budget needed)
- **Delete remote branches** (git proxy returns 403)
- **Verify GA4 ingestion in production** (test browser blocks/503s; user must test from clean device)

## What I (the agent) routinely do

- Edit `index.html`, `for-*.html`, `comparisons/*.html`, playbook .md files
- Wire analytics events with `gtag.js` directly (NOT GTM — there's no GTM container)
- Add sitemap entries on every new public page
- Add `data-product` attributes to YouTube links so `video_play` events fire with accurate product keys
- Open PRs with squash-ready titles + test plans + session URL
- Subscribe-and-respond to PR webhooks (CI checks + review comments)

---

## External dependencies (if these change, things break)

| Dependency | Where it's referenced |
|---|---|
| GA4 property `G-RWJKZXGNPF` | every HTML page's `<head>` |
| YouTube channel `@plainspokenfoundrynine` | every Watch Demo button + Sitemap |
| Backend at `https://app.plainspokenfoundrynine.com/store-api/*` | `index.html` checkout, contact form, calculator lead capture |
| Stripe (live mode) | `store_api.py` webhook handler |
| Resend (transactional email) | `store_api.py` welcome and notification emails |
| GitHub Pages hosting custom domain | `.github/workflows/deploy.yml` |

---

## How to pick up this project from scratch

1. Read this file end to end
2. Read `SALES_PLAN.md` §6 Sales Motion — the strategic constraint everything else flows from
3. Skim `index.html` lines 100–600 to see the storefront structure
4. Look at the most recent PR diff to see what's currently in motion
5. Check open PRs (PR #13 as of last update) before opening anything new
6. If unsure about strategy: ask the founder. If unsure about implementation: read the most recent matching PR for a pattern.
