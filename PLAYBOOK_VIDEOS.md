# PF9 Per-App Video Production Package

**Purpose:** every script, shot list, voiceover spec, and YouTube metadata block needed to produce the product videos that drive PF9's video-led funnel (`SALES_PLAN.md` §6).

**Producer:** Cowork Creative agent (`AGENTS.md` Agent 5) or human operator using the same workflow.

## Production status (as of 2026-05-06)

| App | Status | URL |
|---|---|---|
| FLOWTRACK | ✅ Live | https://youtu.be/VA_TKydOxuQ |
| QUALIFI | ✅ Live | https://youtu.be/42TdtdcaUnk |
| SHIFTLOG | ✅ Live | https://youtu.be/AZA8wj916Sc |
| INSPECTR | ✅ Live | https://youtu.be/_1SQDCRjhf0 |
| LANDLORDR | ✅ Live | https://youtu.be/lpA0qVSOyBY |
| TENANTLINK | ✅ Live | https://youtu.be/w_02sqH1n3s |
| PROPERTY_BUNDLE | ✅ Live | https://youtu.be/63TRUxSKeho |
| EXTRACTR | ✅ Live | https://youtu.be/0rpvA708nFI |
| COMPLI | ✅ Live | https://youtu.be/Y-gxxXJ-EkQ |
| REPORTR | ⏳ In production | — |
| PERMITR | ⏳ In production | — |
| TASKFLOW | ⏳ In production | — |
| OPSIQ | ⏳ In production | — |
| SUPPORTR | ⏳ In production | — |
| MAINTAINR | ⏳ In production | — |

When a new video ships, add the URL to the table above, swap the `href` on the matching `<a data-product="...">Watch Demo</a>` in `index.html`, and append a `VideoObject` entry to the JSON-LD block in `<head>`.

**Production pipeline:**
1. Run `python tools/capture_screenshots.py --variant video_1080p` to populate `./screenshots/`
2. Generate voiceover with ElevenLabs using the voice + script in each section below
3. Run `python tools/compose_video.py --voiceover audio/{slug}.mp3 --shots {ordered shots} --output marketing/{slug}.mp4`
4. Upload to YouTube as **unlisted** with the title + description + tags from this file
5. Submit YouTube URL + thumbnail to approval queue
6. On approval: flip to public; update the `data-product`-matching `<a>` href on the storefront from the channel root to the specific video URL

---

## Global standards (apply to every video)

- **Length:** 60 seconds preferred, 90 seconds maximum. Sub-60 outperforms long-form on every funnel KPI.
- **Resolution:** 1920×1080, 30fps, H.264 + AAC, MP4
- **Aspect ratio:** 16:9 (we are not making vertical short-form on the same pipeline; that's a separate workflow)
- **Voice:** ElevenLabs library voice `Daniel` (deep, calm, slightly conversational) for manufacturing/operations apps; `Charlotte` (warm, professional) for property apps. Never clone the founder's voice.
- **Pace:** 145–155 words/min. Don't rush; the value of these videos is *clarity*, not energy.
- **Music:** none. Voice + UI screenshots only. Music adds nothing and complicates licensing.
- **Captions:** burned-in, bottom-third, white text on translucent black, 36pt min. ~70% of YouTube viewing has sound off.
- **End frame (held 3 seconds):** PF9 logo, app name, price, single line: `Subscribe at store.plainspokenfoundrynine.com`
- **Forbidden:** competitor names spoken or shown, "enterprise-grade," "AI replaces operator," fake testimonials, fake user names in screenshots
- **Required disclosures:** none for product videos. (Voicemails — covered separately in `AGENTS.md` §Compliance flag — do require disclosure.)

---

## Script template (every app uses this five-beat structure)

| Beat | Seconds | Job |
|---|---|---|
| **Hook** | 0–6 | Specific, recognizable pain. No company name yet. |
| **Stakes** | 6–15 | Why the pain matters: cost, time, risk. |
| **Solution** | 15–45 | Show the app doing the thing. Real screenshots, narrated. |
| **Proof** | 45–55 | Price, what's included, the differentiator (flat rate, no per-user fees). |
| **CTA** | 55–60 | Subscribe URL + 14-day money-back. |

---

# Manufacturing Suite

## 1. SHIFTLOG — $49/mo

**Tagline:** *Walk in at 6am. See what happened on second shift.*
**Slug:** `shiftlog`
**Voice:** Daniel
**Length target:** 60 seconds

### Voiceover script (155 words)

> It's 6 a.m. You're walking the floor. Second shift left four hours ago.
>
> Right now, the only way to find out what actually happened — incidents, late jobs, machine flags — is to track down three supervisors and read four whiteboards.
>
> By the time you've pieced it together, the day's already gone.
>
> SHIFTLOG fixes that. Supervisors log handoffs, incidents, and crew notes from a tablet at end-of-shift. The next shift's lead opens one screen and sees everything that matters in fifteen seconds.
>
> Search by date, by line, by person. Photo and video attachments. Auto-rolling summary on the TV in the break room.
>
> Forty-nine dollars a month. Flat. Unlimited supervisors, unlimited shifts. No per-user fees, ever. Most shops are running it the same week they sign up.
>
> Subscribe at store.plainspokenfoundrynine.com. Fourteen-day money-back, no questions asked.

### Shot list

| # | Time | Shot | Source |
|---|---|---|---|
| 1 | 0:00–0:06 | Stock-style shot of a shop floor at dawn (Pixa-generated, abstract; no real people) | Pixa |
| 2 | 0:06–0:15 | Whiteboard scribble overlay; clipboard photo (Pixa) | Pixa |
| 3 | 0:15–0:25 | SHIFTLOG end-of-shift form being filled in | `screenshots/shiftlog_video_1080p_*.png` shot A (form) |
| 4 | 0:25–0:35 | SHIFTLOG handoff feed — incidents + notes | shot B (feed) |
| 5 | 0:35–0:45 | SHIFTLOG search and filter view | shot C (search) |
| 6 | 0:45–0:55 | TV display mode summary | shot D (TV mode) |
| 7 | 0:55–0:60 | End frame: PF9 logo + "SHIFTLOG · $49/mo · store.plainspokenfoundrynine.com" | static |

### YouTube metadata

- **Title:** `SHIFTLOG — End-of-Shift Handoffs in 15 Seconds ($49/mo Flat)`
- **Description:**
  > Stop tracking down supervisors at 6 a.m. SHIFTLOG digitizes shift handoffs, incidents, and crew notes for $49/month flat — no per-user fees, no setup project, no enterprise contract.
  >
  > Built for small-to-mid manufacturers. 14-day money-back guarantee.
  >
  > → Subscribe: https://store.plainspokenfoundrynine.com
  > → Other apps: https://www.youtube.com/@plainspokenfoundrynine
  >
  > 0:00 The 6 a.m. problem
  > 0:15 What SHIFTLOG does
  > 0:45 Pricing
  > 0:55 Subscribe
- **Tags:** `manufacturing software, shift handoff, MES alternative, plant manager tools, shop floor software, shift management app, manufacturing SaaS, no per user fee software`
- **Thumbnail copy:** `6 AM. WHAT HAPPENED LAST NIGHT? · SHIFTLOG · $49/mo`

---

## 2. FLOWTRACK — $99/mo

**Tagline:** *Inventory that doesn't live in a spreadsheet.*
**Slug:** `flowtrack`
**Voice:** Daniel
**Length target:** 75 seconds

### Voiceover script (185 words)

> If you're tracking inventory in a spreadsheet, here's what's true.
>
> The count is always wrong by Wednesday. Re-orders happen by gut. Lot traceability is whoever remembered to write it down.
>
> The "real" inventory software costs five hundred dollars a month per user and takes three months to set up. So you stay on the spreadsheet.
>
> FLOWTRACK is the in-between. Ninety-nine dollars a month, flat. Unlimited users.
>
> Scan in raw materials. Track WIP through the line. Flag finished goods. Barcode-driven, mobile-first, works offline.
>
> Reorder points trigger automatically. Lot history is searchable in two clicks. CSV export to QuickBooks. API to anything else.
>
> Most shops import their existing spreadsheet on day one and are running barcodes the next morning.
>
> No per-user fees. No setup project. No quote.
>
> Subscribe at store.plainspokenfoundrynine.com. Fourteen-day money-back, full refund within two weeks if it's not the right fit.

### Shot list

| # | Time | Shot | Source |
|---|---|---|---|
| 1 | 0:00–0:08 | Pixa: spreadsheet zoom-in with messy cells | Pixa |
| 2 | 0:08–0:18 | Pixa: "$500/mo per user" struck through; clock graphic | Pixa |
| 3 | 0:18–0:30 | FLOWTRACK barcode scan view | `screenshots/flowtrack_*` shot A |
| 4 | 0:30–0:42 | FLOWTRACK WIP tracking | shot B |
| 5 | 0:42–0:55 | Reorder point alert + lot history detail | shots C + D |
| 6 | 0:55–1:10 | CSV export modal + API docs glimpse | shot E |
| 7 | 1:10–1:15 | End frame | static |

### YouTube metadata

- **Title:** `FLOWTRACK — Inventory Software for Small Manufacturers ($99/mo, Unlimited Users)`
- **Description:**
  > Inventory tracking, WIP, and barcode scanning for $99/month flat. No per-user fees. No setup project. Built for small-to-mid manufacturers tired of spreadsheets and $500/seat MES quotes.
  >
  > 14-day money-back guarantee.
  >
  > → Subscribe: https://store.plainspokenfoundrynine.com
  > → All PF9 apps: https://www.youtube.com/@plainspokenfoundrynine
- **Tags:** `inventory management software, manufacturing inventory app, barcode scanning small business, WIP tracking, MES alternative small shop, manufacturing SaaS no per user fee`
- **Thumbnail copy:** `INVENTORY · OUT OF EXCEL · $99/mo FLAT`

---

## 3. QUALIFI — $79/mo

**Tagline:** *Quality management without the paper.*
**Slug:** `qualifi`
**Voice:** Daniel
**Length target:** 70 seconds

### Voiceover script (170 words)

> Paper inspection forms are a tax. Time to fill out, time to file, time to find again when the customer calls back six weeks later asking about lot 4-7-2.
>
> QUALIFI replaces the paper. Seventy-nine dollars a month, flat.
>
> Inspectors fill digital forms on a tablet. Photos and signatures attach to the record. NCRs and CAPAs route through approval automatically. SPC charts update from the data you're already entering.
>
> Supplier quality scorecards roll up by line, by part, by week.
>
> When the customer calls about lot 4-7-2, you find it in three seconds, not three hours.
>
> Unlimited inspectors. Unlimited forms. Unlimited records. No per-user fees.
>
> Most shops are running their first digital inspection inside an hour of subscribing.
>
> Subscribe at store.plainspokenfoundrynine.com. Fourteen-day money-back, full refund within two weeks if QUALIFI isn't pulling weight.

### Shot list

| # | Time | Shot | Source |
|---|---|---|---|
| 1 | 0:00–0:08 | Pixa: stack of paper forms | Pixa |
| 2 | 0:08–0:18 | QUALIFI tablet inspection form | `screenshots/qualifi_*` shot A |
| 3 | 0:18–0:30 | NCR / CAPA workflow approval view | shot B |
| 4 | 0:30–0:42 | SPC chart populating | shot C |
| 5 | 0:42–0:55 | Supplier scorecard | shot D |
| 6 | 0:55–1:05 | Search by lot — instant result | shot E |
| 7 | 1:05–1:10 | End frame | static |

### YouTube metadata

- **Title:** `QUALIFI — Digital Quality Management for Small Manufacturers ($79/mo)`
- **Description:**
  > Replace paper inspection forms, NCR/CAPA workflows, and SPC charting for $79/month flat. No per-user fees. Built for small-to-mid manufacturers.
  >
  > → Subscribe: https://store.plainspokenfoundrynine.com
- **Tags:** `quality management software, NCR CAPA software, SPC charting small business, digital inspection forms, manufacturing QMS`
- **Thumbnail copy:** `PAPER FORMS → DIGITAL · QUALIFI · $79/mo`

---

## 4. REPORTR — $59/mo

**Tagline:** *Operations dashboards without a BI consultant.*
**Slug:** `reportr`
**Voice:** Daniel
**Length target:** 60 seconds

### Voiceover script (150 words)

> Most operations dashboards live in a BI tool that costs ten thousand dollars a year and a consultant who built it twice.
>
> REPORTR is the same dashboard, drag-and-drop, fifty-nine dollars a month.
>
> Connect FLOWTRACK, SHIFTLOG, QUALIFI, or your existing CSVs. Drop tiles for production, scrap, downtime, on-time-delivery. Schedule reports to hit your inbox at six a.m. every Monday.
>
> TV display mode rotates the right view to the right screen — production for the line, KPIs for the office, quality for the lab.
>
> No data warehouse. No semantic layer. No consultant.
>
> Fifty-nine dollars a month, unlimited dashboards, unlimited viewers.
>
> Subscribe at store.plainspokenfoundrynine.com.

### Shot list

| # | Time | Shot | Source |
|---|---|---|---|
| 1 | 0:00–0:06 | Pixa: complex BI dashboard with "$10k/yr" overlay | Pixa |
| 2 | 0:06–0:18 | REPORTR drag-and-drop tile builder | `screenshots/reportr_*` shot A |
| 3 | 0:18–0:30 | Connectors panel | shot B |
| 4 | 0:30–0:42 | Scheduled email report | shot C |
| 5 | 0:42–0:54 | TV display mode | shot D |
| 6 | 0:54–0:60 | End frame | static |

### YouTube metadata

- **Title:** `REPORTR — Drag-and-Drop Operations Dashboards ($59/mo)`
- **Description:**
  > Operations dashboards without a BI consultant. Connect your inventory, shift, and quality data. Drop tiles. Schedule reports. $59/month flat.
  >
  > → Subscribe: https://store.plainspokenfoundrynine.com
- **Tags:** `operations dashboard, BI alternative small business, drag and drop dashboard, manufacturing KPI software, scheduled reports`
- **Thumbnail copy:** `DASHBOARDS WITHOUT A CONSULTANT · $59/mo`

---

## 5. INSPECTR — $49/mo

**Tagline:** *Field inspections from your phone.*
**Slug:** `inspectr`
**Voice:** Daniel
**Length target:** 60 seconds

### Voiceover script (150 words)

> Field inspections live on a clipboard, a camera roll, and a memory.
>
> Then someone has to type it up.
>
> INSPECTR collapses that into one app on the inspector's phone. Custom checklists per asset, per route, per customer. Real-time failure logging. Photo capture inline. Geo-stamp, time-stamp, signature.
>
> Inspector finishes the route. Report's done before the truck pulls back into the yard.
>
> PDF export, CSV, or push the whole record into REPORTR for trend analysis.
>
> Forty-nine dollars a month. Unlimited inspectors. Unlimited inspections. Works offline — syncs when the phone reconnects.
>
> Subscribe at store.plainspokenfoundrynine.com.

### Shot list

| # | Time | Shot | Source |
|---|---|---|---|
| 1 | 0:00–0:08 | Pixa: clipboard + phone + truck | Pixa |
| 2 | 0:08–0:20 | INSPECTR mobile checklist | `screenshots/inspectr_*` shot A |
| 3 | 0:20–0:32 | Failure logging with photo + signature | shot B |
| 4 | 0:32–0:44 | Auto-generated PDF report | shot C |
| 5 | 0:44–0:54 | Offline → sync confirmation | shot D |
| 6 | 0:54–0:60 | End frame | static |

### YouTube metadata

- **Title:** `INSPECTR — Field Inspection Software for $49/mo (Unlimited Inspectors)`
- **Tags:** `field inspection app, mobile inspection software, asset inspection, route inspection software, offline inspection app`
- **Thumbnail copy:** `FIELD INSPECTIONS · ONE APP · $49/mo`

---

# Property Suite

## 6. LANDLORDR — $89/mo

**Tagline:** *Property management without per-door fees.*
**Slug:** `landlordr`
**Voice:** Charlotte
**Length target:** 75 seconds

### Voiceover script (180 words)

> If you have eight rental units, you don't need a fifty-thousand-dollar property management system.
>
> But every quote you get is per-door. Two dollars a unit. Five. Ten. Plus a setup fee. Plus an integration consultant.
>
> LANDLORDR is the alternative. Eighty-nine dollars a month, flat. Unlimited units. Unlimited tenants. Unlimited team members.
>
> Track leases, rent ledgers, maintenance tickets, and vendor invoices in one place. Generate the rent roll, the owner statement, and the 1099-ready vendor summary in one click.
>
> Tenant gets their own portal — pay rent, submit maintenance, see lease docs. That's TENANTLINK, included if you bundle the suite.
>
> Whether you manage five units or five hundred, the price doesn't change.
>
> Subscribe at store.plainspokenfoundrynine.com. Fourteen-day money-back, full refund within two weeks.

### Shot list

| # | Time | Shot | Source |
|---|---|---|---|
| 1 | 0:00–0:08 | Pixa: per-door pricing math, struck through | Pixa |
| 2 | 0:08–0:20 | LANDLORDR property + unit list | `screenshots/landlordr_*` shot A |
| 3 | 0:20–0:32 | Lease detail with rent ledger | shot B |
| 4 | 0:32–0:45 | Maintenance ticket workflow | shot C |
| 5 | 0:45–0:58 | Owner statement / rent roll PDF | shot D |
| 6 | 0:58–1:10 | Tenant portal preview | shot E |
| 7 | 1:10–1:15 | End frame: "$119/mo with TENANTLINK bundle" | static |

### YouTube metadata

- **Title:** `LANDLORDR — Property Management Software, No Per-Door Fees ($89/mo)`
- **Description:**
  > Flat-rate property management for independent landlords. Unlimited units, unlimited tenants, unlimited team members. $89/month for LANDLORDR alone, $119/month bundled with TENANTLINK tenant portal.
  >
  > A Buildium, AppFolio, and DoorLoop alternative for landlords with 5–50 units.
  >
  > → Subscribe: https://store.plainspokenfoundrynine.com/for-landlords.html
  > → Per-door cost calculator: https://store.plainspokenfoundrynine.com/tools/per-door-calculator.html
- **Tags:** `property management software, buildium alternative, appfolio alternative, doorloop alternative, flat rate landlord software, no per unit fee property management`
- **Thumbnail copy:** `NO PER-DOOR FEES · LANDLORDR · $89/mo`

---

## 7. TENANTLINK — $49/mo

**Tagline:** *A tenant portal your tenants will actually use.*
**Slug:** `tenantlink`
**Voice:** Charlotte
**Length target:** 60 seconds

### Voiceover script (150 words)

> Tenants want three things from a portal. Pay rent. Submit a maintenance request. See the lease.
>
> Most landlord software charges you per-tenant for the privilege.
>
> TENANTLINK is forty-nine dollars a month. Flat. Unlimited tenants.
>
> Tenant logs in. Pays rent — ACH, card, autopay. Submits a maintenance request with photos. Pulls up their lease and rent history.
>
> Landlord sees the same data on the back-end, in LANDLORDR.
>
> Email and SMS notifications fire automatically. No paper, no chasing.
>
> Or bundle TENANTLINK with LANDLORDR for one hundred and nineteen dollars a month — the full property suite for less than what most software charges per door.
>
> Subscribe at store.plainspokenfoundrynine.com.

### Shot list

| # | Time | Shot | Source |
|---|---|---|---|
| 1 | 0:00–0:08 | Pixa: tenant phone with messy email thread | Pixa |
| 2 | 0:08–0:20 | TENANTLINK rent payment screen | `screenshots/tenantlinkr_*` shot A |
| 3 | 0:20–0:32 | Maintenance request with photo upload | shot B |
| 4 | 0:32–0:42 | Lease + payment history view | shot C |
| 5 | 0:42–0:54 | Landlord-side notification feed | shot D |
| 6 | 0:54–0:60 | End frame | static |

### YouTube metadata

- **Title:** `TENANTLINK — Tenant Portal for Independent Landlords ($49/mo Flat)`
- **Tags:** `tenant portal software, online rent payment, tenant maintenance request app, small landlord software, flat rate tenant portal`
- **Thumbnail copy:** `RENT · MAINTENANCE · LEASE · ONE PORTAL · $49/mo`

---

## 8. PROPERTY_BUNDLE — $119/mo

**Tagline:** *The full property suite, $119/month flat.*
**Slug:** `property-bundle`
**Voice:** Charlotte
**Length target:** 60 seconds

### Voiceover script (150 words)

> If you manage rental property, here's the math.
>
> Buildium starts at sixty-two dollars plus per-unit fees. AppFolio is fifty-unit minimum. DoorLoop jumps to a hundred and eighty-nine dollars at ten units.
>
> The PF9 Property Suite is one hundred and nineteen dollars a month. Flat. At any unit count.
>
> You get LANDLORDR — leases, rent ledgers, maintenance, vendor invoices, owner statements. Plus TENANTLINK — the tenant portal for online rent and self-service.
>
> Save eighteen dollars a month against subscribing to each app separately. Save thousands a year against per-door pricing.
>
> Five units, five hundred. The price stays the same.
>
> Subscribe at store.plainspokenfoundrynine.com.

### Shot list

| # | Time | Shot | Source |
|---|---|---|---|
| 1 | 0:00–0:08 | Pixa: pricing comparison chart (PF9 vs three competitors, no names) | Pixa |
| 2 | 0:08–0:20 | LANDLORDR dashboard | `screenshots/landlordr_*` |
| 3 | 0:20–0:30 | TENANTLINK rent payment | `screenshots/tenantlinkr_*` |
| 4 | 0:30–0:45 | Bundle pricing callout from storefront | `screenshots/store-home_*` |
| 5 | 0:45–0:54 | Per-door calculator preview | `screenshots/store-home_*` (calculator section) |
| 6 | 0:54–0:60 | End frame | static |

### YouTube metadata

- **Title:** `PF9 Property Suite — Landlordr + Tenantlink for $119/mo Flat`
- **Tags:** `property management bundle, flat rate landlord software, buildium alternative, no per door property management`
- **Thumbnail copy:** `5 UNITS OR 500 · $119/mo FLAT`

---

## 9. PERMITR — $299/mo

**Tagline:** *Permit tracking for property managers and contractors.*
**Slug:** `permitr`
**Voice:** Charlotte
**Length target:** 75 seconds

### Voiceover script (180 words)

> Permits expire. Inspections get missed. Renewal letters land on someone's desk and stay there. Then the city calls.
>
> PERMITR tracks every permit, inspection, and certificate across every property and contractor you manage. Renewal alerts fire thirty, sixty, ninety days out. Inspection schedules sync to the team calendar. Document storage links every cert to the property and the unit.
>
> When a tenant complaint comes in or a sale closes, the entire compliance file is one click away.
>
> Two hundred ninety-nine dollars a month. Unlimited permits, unlimited properties, unlimited team members.
>
> Compared to a paid compliance consultant or a missed renewal fine, this is the cheapest insurance you'll buy this year.
>
> Subscribe at store.plainspokenfoundrynine.com. Fourteen-day money-back if PERMITR isn't earning its keep.

### Shot list

| # | Time | Shot | Source |
|---|---|---|---|
| 1 | 0:00–0:10 | Pixa: stack of unopened renewal envelopes | Pixa |
| 2 | 0:10–0:25 | PERMITR permit list with status badges | `screenshots/permitr_*` shot A |
| 3 | 0:25–0:40 | Renewal alert detail view | shot B |
| 4 | 0:40–0:55 | Inspection schedule + calendar sync | shot C |
| 5 | 0:55–1:10 | Compliance file with linked documents | shot D |
| 6 | 1:10–1:15 | End frame | static |

### YouTube metadata

- **Title:** `PERMITR — Permit & Inspection Tracking for Property Managers ($299/mo)`
- **Tags:** `permit tracking software, inspection management, property compliance software, contractor permit tracking, renewal alert software`
- **Thumbnail copy:** `PERMITS · INSPECTIONS · CERTS · ONE APP · $299/mo`

---

## 10. TASKFLOW — $69/mo

**Tagline:** *Property maintenance dispatching without the spreadsheet.*
**Slug:** `taskflow`
**Voice:** Charlotte
**Length target:** 60 seconds

### Voiceover script (150 words)

> When a tenant submits a maintenance request, the next sixty minutes decide whether they renew the lease.
>
> TASKFLOW dispatches it. Vendor gets the request, the photos, and the address on their phone. Tenant gets an ETA. You see the whole queue on one screen — open, in progress, awaiting parts, completed.
>
> Sixty-nine dollars a month. Unlimited vendors. Unlimited tickets.
>
> Vendor scorecards roll up automatically. Time-to-resolution reports hit your inbox weekly. Tenant satisfaction tracked per ticket.
>
> Pairs cleanly with TENANTLINK on the tenant side and LANDLORDR on the property side.
>
> Subscribe at store.plainspokenfoundrynine.com.

### Shot list

| # | Time | Shot | Source |
|---|---|---|---|
| 1 | 0:00–0:08 | Pixa: text message chain on a phone | Pixa |
| 2 | 0:08–0:20 | TASKFLOW dispatch board | `screenshots/taskflow_*` shot A |
| 3 | 0:20–0:32 | Vendor mobile view of ticket | shot B |
| 4 | 0:32–0:44 | Tenant ETA notification preview | shot C |
| 5 | 0:44–0:54 | Vendor scorecard | shot D |
| 6 | 0:54–0:60 | End frame | static |

### YouTube metadata

- **Title:** `TASKFLOW — Property Maintenance Dispatch Software ($69/mo)`
- **Tags:** `property maintenance software, work order software, vendor dispatch app, rental maintenance tracking`
- **Thumbnail copy:** `MAINTENANCE TICKETS · DISPATCHED IN MINUTES · $69/mo`

---

# Operations & AI

## 11. OPSIQ — from $79/mo

**Tagline:** *Ask your operations data a question. Get an answer.*
**Slug:** `opsiq`
**Voice:** Daniel
**Length target:** 75 seconds

### Voiceover script (185 words)

> Most operations dashboards answer the questions you already knew to ask.
>
> OPSIQ answers the ones you haven't.
>
> "Which line ran below target last month and why." "Which supplier missed delivery on parts that ended up in our top defect category." "What's our actual labor cost per unit on the third shift."
>
> You type the question. OPSIQ returns the answer, the underlying tiles, and the trend.
>
> Plain English in. Procurement, production, quality, workforce, maintenance — connected through your existing PF9 apps or via CSV import.
>
> Three tiers. Seventy-nine dollars for the team plan, one hundred ninety-nine for multi-site, three hundred ninety-nine for full ops intelligence with custom alerts and forecasting.
>
> No data warehouse. No prompt engineering. No analyst hire.
>
> Subscribe at store.plainspokenfoundrynine.com. Fourteen-day money-back, full refund if OPSIQ isn't faster than asking your analyst.

### Shot list

| # | Time | Shot | Source |
|---|---|---|---|
| 1 | 0:00–0:10 | Pixa: dashboard with question marks above tiles | Pixa |
| 2 | 0:10–0:25 | OPSIQ natural-language query box being typed in | `screenshots/opsiq_*` shot A |
| 3 | 0:25–0:40 | Returned answer with tiles | shot B |
| 4 | 0:40–0:55 | Connected sources panel | shot C |
| 5 | 0:55–1:10 | Pricing tier comparison | static |
| 6 | 1:10–1:15 | End frame | static |

### YouTube metadata

- **Title:** `OPSIQ — Ask Your Operations Data a Question (from $79/mo)`
- **Tags:** `operations intelligence, AI dashboard, natural language BI, manufacturing analytics, ask AI operations data`
- **Thumbnail copy:** `TYPE THE QUESTION · GET THE ANSWER · OPSIQ`

---

## 12. EXTRACTR — $149/mo

**Tagline:** *Document data extraction without the manual entry.*
**Slug:** `extractr`
**Voice:** Daniel
**Length target:** 60 seconds

### Voiceover script (150 words)

> POs, packing slips, COIs, invoices. Every one of them is a document somebody has to read, then re-type into a system.
>
> EXTRACTR reads them for you. Drag the PDF in, and the structured fields come out — vendor, line items, due dates, certificate expiration, whatever the document carries.
>
> Push the structured data into FLOWTRACK, LANDLORDR, REPORTR, or your existing system via CSV or API.
>
> One hundred forty-nine dollars a month. Unlimited documents. No per-page fees.
>
> Compared to a clerk re-typing or a per-page OCR service, EXTRACTR pays for itself the first week.
>
> Subscribe at store.plainspokenfoundrynine.com.

### Shot list

| # | Time | Shot | Source |
|---|---|---|---|
| 1 | 0:00–0:08 | Pixa: stack of PDFs | Pixa |
| 2 | 0:08–0:22 | EXTRACTR drag-and-drop import | `screenshots/extractr_*` shot A |
| 3 | 0:22–0:38 | Structured field extraction view | shot B |
| 4 | 0:38–0:52 | Push-to-FLOWTRACK button + confirmation | shot C |
| 5 | 0:52–0:60 | End frame | static |

### YouTube metadata

- **Title:** `EXTRACTR — Document Data Extraction for Operations ($149/mo Unlimited)`
- **Tags:** `document data extraction, AI OCR, invoice data extraction, PDF to structured data, business operations automation`
- **Thumbnail copy:** `PDF IN · STRUCTURED DATA OUT · $149/mo`

---

## 13. SUPPORTR — $79/mo

**Tagline:** *A help desk that doesn't price you out.*
**Slug:** `supportr`
**Voice:** Daniel
**Length target:** 60 seconds

### Voiceover script (150 words)

> Most help desk software charges per agent. Eighty dollars. A hundred. More if you want the AI features.
>
> SUPPORTR is seventy-nine dollars a month. Flat. Unlimited agents.
>
> Inbound email, web form, and SMS land in the same queue. Tickets route by tag, by priority, by team. SLA timers track every open ticket. Customer-side portal lets the customer see their own ticket history without an account.
>
> Reports out of the box — first response time, resolution time, agent load, top issue categories.
>
> If you have a small team handling support and you don't want a per-agent contract, SUPPORTR is the unlock.
>
> Subscribe at store.plainspokenfoundrynine.com.

### Shot list

| # | Time | Shot | Source |
|---|---|---|---|
| 1 | 0:00–0:08 | Pixa: per-agent pricing chart, struck out | Pixa |
| 2 | 0:08–0:22 | SUPPORTR ticket queue | `screenshots/supportr_*` shot A |
| 3 | 0:22–0:36 | Ticket detail with thread + tags | shot B |
| 4 | 0:36–0:48 | SLA dashboard | shot C |
| 5 | 0:48–0:54 | Customer portal view | shot D |
| 6 | 0:54–0:60 | End frame | static |

### YouTube metadata

- **Title:** `SUPPORTR — Help Desk Software, Unlimited Agents ($79/mo)`
- **Tags:** `help desk software no per agent fee, support ticket software, customer support tool small business, flat rate help desk`
- **Thumbnail copy:** `UNLIMITED AGENTS · $79/mo FLAT · SUPPORTR`

---

## 14. MAINTAINR — $99/mo

**Tagline:** *Preventive maintenance that doesn't live on a sticky note.*
**Slug:** `maintainr`
**Voice:** Daniel
**Length target:** 60 seconds

### Voiceover script (150 words)

> Preventive maintenance fails at the calendar.
>
> Either the calendar lives in someone's head — and gets missed — or it lives in a CMMS that costs three hundred a month and takes six weeks to set up.
>
> MAINTAINR is ninety-nine dollars a month. Asset list, schedule, work orders, parts inventory.
>
> Schedule weekly, monthly, quarterly, hours-based, or condition-based PMs. Auto-generate work orders. Tech checks off the steps on a phone, logs parts used, attaches photos.
>
> When something breaks anyway, the failure history is right there next to the asset.
>
> Unlimited assets. Unlimited techs. No per-user fees.
>
> Subscribe at store.plainspokenfoundrynine.com.

### Shot list

| # | Time | Shot | Source |
|---|---|---|---|
| 1 | 0:00–0:08 | Pixa: sticky notes on a piece of equipment | Pixa |
| 2 | 0:08–0:20 | MAINTAINR asset list | `screenshots/maintainr_*` shot A |
| 3 | 0:20–0:34 | PM schedule + auto-generated work order | shot B |
| 4 | 0:34–0:48 | Tech mobile view checking off PM steps | shot C |
| 5 | 0:48–0:54 | Failure history view | shot D |
| 6 | 0:54–0:60 | End frame | static |

### YouTube metadata

- **Title:** `MAINTAINR — Preventive Maintenance Software, Unlimited Assets ($99/mo)`
- **Tags:** `preventive maintenance software, CMMS small business, work order software, asset management software, no per user CMMS`
- **Thumbnail copy:** `PMs · WORK ORDERS · ASSETS · $99/mo`

---

# Production order (priority)

Produce in this order — gives the funnel the most leverage per video as it comes online:

1. **SHIFTLOG** — lowest price entry point ($49), broadest target audience (any manufacturer with shifts)
2. **FLOWTRACK** — manufacturing flagship, most search demand
3. **LANDLORDR** — anchors the property vertical with `for-landlords.html` and the per-door calculator
4. **PROPERTY_BUNDLE** — converts the LANDLORDR landing-page traffic at higher AOV
5. **OPSIQ** — highest-AOV product; demand-gen for the multi-site ICP
6. **QUALIFI** through **MAINTAINR** — fill out the catalog as production capacity allows

Goal: ship the top 5 within 14 days. Don't wait for the full catalog before launching the funnel.

---

# Approval checkpoints

Per `AGENTS.md` Agent 5 approval rules:

- **First video produced:** human reviews voice + script template + visual style. Approval applies to the same voice + visual treatment for subsequent videos.
- **Each subsequent video:** approve only the script and shot list (already-approved voice and style auto-apply).
- **Any new voice (e.g., Charlotte for the property suite if Daniel was approved first):** full re-approval.
- **Any title or thumbnail copy that names a competitor or makes a claim outside `SALES_PLAN.md` §4 guardrails:** reject.

---

# Hand-back schema (when a video ships)

When the Cowork Creative agent or the human producer publishes a video, they update the storefront so the right card links to the right video. Concretely:

1. In `index.html`, find the product card (`onclick="openSubscribe('{PRODUCT}', ...)"`)
2. Change the adjacent `<a href="https://www.youtube.com/@plainspokenfoundrynine">Watch Demo</a>` to `<a href="https://youtu.be/{video_id}" data-product="{PRODUCT}">Watch Demo</a>`
3. The existing `video_play` analytics listener already infers product from the card heading, so it keeps working

Same pattern for `for-landlords.html` (one CTA, points to `landlordr` or `property-bundle` video).
