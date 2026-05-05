# Outbound Sequence — ICP-1 Manufacturing

**Target:** Plant Manager, Operations Director, Plant Superintendent, GM at 20–250 employee discrete or light-process manufacturers in North America.
**Goal of the sequence:** drive a `video_play` event followed by a Subscribe within 14 days. **There is no live demo and no booking call** — the funnel is video → Stripe checkout, end to end self-serve.
**Duration:** 14 business days, 4 emails + 2 LinkedIn touches. No phone call (no demo to book).
**Tooling:** Instantly / Smartlead / Apollo for email, Sales Navigator for LinkedIn, CRM of record for disposition.
**Reply-routing rule:** any human reply = stop sequence, route to founder for a 1:1 reply. The reply is rare; treat each one carefully.

---

## Pre-send checklist

Before a contact enters the sequence:
- [ ] Company is 20–250 employees on LinkedIn
- [ ] Title matches target list (no VP Engineering, no IT Director — wrong buyer)
- [ ] Website confirms discrete/light-process manufacturing (not food/pharma/automotive-tier-1)
- [ ] Not already in CRM in any stage
- [ ] Email verified (bounce rate <2% on list)

Personalization: **one** concrete detail per prospect, pulled from their LinkedIn or company site. Don't personalize more — it doesn't improve reply rate and slows the sequence.

---

## Day 1 — Email 1: Problem, no pitch

**Subject:** tracking shifts in Excel at {{company}}?

**Body:**

Hey {{first_name}},

Quick one — most {{industry_descriptor, e.g. "small job shops"}} I talk to are still tracking shift handoffs and inventory counts in spreadsheets. Not because they want to, but because the "real" MES quotes come back at $50k and 6 months.

Is that roughly the case at {{company}}?

If yes, I built a couple of small flat-rate apps you can subscribe to in 60 seconds. No demo to sit through, no sales call. Worth a 90-second video?

{{sender_first}}

---
**Why this works:** 70-word cold email, asks a yes/no question, no link in the first email, sets expectation that there's no sales-cycle pain ahead.

---

## Day 2 — LinkedIn: Connection request

**Note (300 char max):**

Hey {{first_name}} — came across {{company}} while looking at {{region/state}} manufacturers. Running a small flat-rate SaaS for shops your size (inventory, shifts, quality). Not pitching in the connect — just useful to have in the network.

**Rule:** never pitch in the connect note. Accept rate collapses.

---

## Day 4 — Email 2: Video link

**Subject:** re: tracking shifts in Excel at {{company}}

**Body:**

{{first_name}} — following up on the note from Monday.

Quick context, since you didn't ask:

- **SHIFTLOG** — $49/mo flat, digital shift handoffs, crew notes, incident log
- **FLOWTRACK** — $99/mo flat, inventory + WIP + barcodes
- **QUALIFI** — $79/mo flat, inspections, NCRs, CAPAs
- Bundle the five apps for $249/mo. No per-seat charges, ever.

90-second video on SHIFTLOG: {{youtube_shiftlog_url}}

If the price-per-user thing has been blocking you on software like this, the video is the shortest path to a yes or no — no signup, no call.

{{sender_first}}

---
**Why this works:** delivers the differentiator (flat pricing) as concrete numbers, gives a single-click education path, no friction.

---

## Day 6 — LinkedIn: Message after accept

**Only send if connection was accepted.**

Thanks for connecting {{first_name}}. Won't flood you — if shift or inventory tracking is on the list for this quarter, here's the 90-second SHIFTLOG video: {{youtube_shiftlog_url}}

Subscribe in two clicks if it fits, or ignore. No hard feelings either way.

---

## Day 9 — Email 3: Specific outcome + subscribe link

**Subject:** what second shift actually did last night

**Body:**

{{first_name}},

The thing the videos cover is one outcome: how a plant manager walks in at 6am and sees, on one screen, what happened on second and third shift — incidents, production, inventory moves, QA flags — instead of tracking down three supervisors.

That's SHIFTLOG + REPORTR together, $108/mo total. Both videos and the subscribe links are here:

→ SHIFTLOG ($49/mo): {{youtube_shiftlog_url}}
→ REPORTR ($59/mo): {{youtube_reportr_url}}
→ Or the full 5-app bundle for $249/mo: https://store.plainspokenfoundrynine.com/#bundle

{{sender_first}}

---
**Why this works:** stops selling a product, sells the Monday-morning outcome. Specific time ("6am"), specific pain ("tracking down three supervisors"), specific price, two clear paths to convert.

---

## Day 14 — Email 4: Permission-to-close

**Subject:** should I close the loop?

**Body:**

{{first_name}} — last one from me.

Totally fine if the timing is off. If I don't hear back by Friday I'll assume it's a no-for-now and stop emailing.

If that's wrong, reply with a one-liner and I'll pick it back up.

{{sender_first}}

---
**Why this works:** the breakup gets a reply rate 2-3× higher than any earlier email. No link, no pitch, just a question.

---

## Sequence rules

- **Never send on Monday before 10am or Friday after 2pm** — reply rate tanks
- **Stop on any reply**, even an out-of-office — route to founder
- **Cap at 50 new contacts per sender per day**
- **One domain at a time** — don't hit three people at the same company in the same week
- **A/B test subjects only** (not bodies) — rotate subject after 200 sends
- **Always link to a YouTube video, never a Loom or self-hosted file** — YouTube has the lowest mobile friction and gives us watch-time analytics for free

---

## KPIs for this sequence

Report weekly in the `SALES_PLAN.md` §7 format:

| Metric | Target |
|---|---|
| Open rate | >45% |
| Click rate (video link) | >6% |
| Video play (per YouTube) | >50% of clicks |
| Reply rate (human) | >5% |
| Subscribes attributed to sequence | 1–2 per 100 sent |
| Unsubscribe rate | <0.5% |

Kill the sequence and rewrite if open rate is under 30% after 500 sends or unsub is over 1%.

---

## Forbidden moves

- No "book a demo" or "grab a slot" — there is no demo and no calendar
- No "just following up"
- No "did you see my last email"
- No fake urgency ("limited beta seats")
- No forwarded-chain fakery ("bumping this to the top")
- No mid-sequence product launches or feature announcements — keep the narrative tight
- No Loom links — YouTube only, for analytics + mobile UX
