# Outbound Sequence — ICP-1 Manufacturing

**Target:** Plant Manager, Operations Director, Plant Superintendent, GM at 20–250 employee discrete or light-process manufacturers in North America.
**Goal of the sequence:** book a 20-minute demo (not a reply, not a download).
**Duration:** 17 business days, 4 emails + 2 LinkedIn touches + 1 optional call.
**Tooling:** Instantly / Smartlead / Apollo for email, Sales Navigator for LinkedIn, CRM of record for disposition.
**Reply-routing rule:** any human reply = stop sequence, move to 1:1 in CRM.

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

**Subject:** tracking shifts in Excel at [Company]?

**Body:**

Hey {{first_name}},

Quick one — most {{industry_descriptor, e.g. "small job shops"}} I talk to are still tracking shift handoffs and inventory counts in spreadsheets. Not because they want to, but because the "real" MES quotes come back at $50k and 6 months.

Is that roughly the case at {{company}}?

If yes, I've got a 20-minute walkthrough of what we built for shops like yours — flat monthly pricing, deploys in a week, no per-user fees. Worth a look?

{{sender_first}}

---
**Why this works:** 68-word cold email, asks a yes/no question, no link, no pitch deck. Tests whether the pain is real before burning a demo slot.

---

## Day 2 — LinkedIn: Connection request

**Note (300 char max):**

Hey {{first_name}} — came across {{company}} while looking at {{region/state}} manufacturers. Running a small SaaS for shops your size (inventory, shifts, quality). Not pitching in the connect — just useful to have in the network.

**Rule:** never pitch in the connect note. Accept rate collapses.

---

## Day 4 — Email 2: Proof point

**Subject:** re: tracking shifts in Excel at {{company}}

**Body:**

{{first_name}} — following up on the note from Monday.

Quick context on what we do, since you didn't ask:

- **SHIFTLOG** — $49/mo flat, digital shift handoffs, crew notes, incident log
- **FLOWTRACK** — $99/mo flat, inventory + WIP + barcodes
- **QUALIFI** — $79/mo flat, inspections, NCRs, CAPAs
- Bundle the five apps for $249/mo. No per-seat charges, ever.

You can try any of them live, no signup, here: https://store.plainspokenfoundrynine.com

If the price-per-user thing is what's been blocking you on software like this, the 20-minute walkthrough is the shortest path to a yes or no.

{{sender_first}}

---
**Why this works:** delivers the differentiator (flat pricing) as concrete numbers, gives a friction-free demo option (the live demo link), keeps the ask the same.

---

## Day 6 — LinkedIn: Message after accept

**Only send if connection was accepted.**

Thanks for connecting {{first_name}}. Won't flood you — if shift or inventory tracking is on the list for this quarter, our store has live demos you can click through without talking to anyone: https://store.plainspokenfoundrynine.com

Otherwise ignore and no hard feelings.

---

## Day 9 — Email 3: Specific value + calendar

**Subject:** 20 minutes — what second shift actually did last night

**Body:**

{{first_name}},

The demo I'd run for {{company}} is 20 minutes and covers one thing: how a plant manager walks in at 6am and sees, on one screen, what happened on second and third shift — incidents, production, inventory moves, QA flags — instead of tracking down three supervisors.

That's SHIFTLOG + REPORTR together, $108/mo total.

Grab a slot that works: {{calendar_link}}

Or tell me the wrong time and I'll suggest two better ones.

{{sender_first}}

---
**Why this works:** stops selling a product, sells the Monday-morning outcome. Specific time ("6am"), specific pain ("tracking down three supervisors"), specific price.

---

## Day 14 — Email 4: Permission-to-close

**Subject:** should I close the loop?

**Body:**

{{first_name}} — last one from me.

Totally fine if the timing is off. If I don't hear back by Friday I'll assume it's a no-for-now and stop emailing.

If that's wrong, reply with a one-liner and I'll pick it back up.

{{sender_first}}

---
**Why this works:** the breakup gets a reply rate 2-3x higher than any earlier email. No link, no pitch, just a question.

---

## Day 17 — Optional phone call (bundle deals only)

**Call trigger:** prospect opened 3+ emails and is at a company with 100+ employees.
**Script for first 20 seconds:**

> "{{First_name}} — {{sender}} from Plainspoken Foundry Nine. I sent a couple emails on shift and inventory tracking for shops your size. Catch you at a bad time, or got 45 seconds?"

If yes: one sentence on what you do, then: "Want me to send a 20-minute walkthrough slot, or is this not on your list right now?"

If no: "Got it. I'll stop the emails. One question before I do — is this not on your list, or is it on someone else's list I should talk to instead?"

---

## Sequence rules

- **Never send on Monday before 10am or Friday after 2pm** — reply rate tanks
- **Stop on any reply**, even an out-of-office — route to a human
- **Cap at 50 new contacts per sender per day**
- **One domain at a time** — don't hit three people at the same company in the same week
- **A/B test subjects only** (not bodies) — rotate subject after 200 sends

---

## KPIs for this sequence

Report weekly in the `SALES_PLAN.md` §7 format:

| Metric | Target |
|---|---|
| Open rate | >45% |
| Reply rate (human) | >8% |
| Positive reply rate | >3% |
| Meetings booked per 100 sent | 2–3 |
| Unsubscribe rate | <0.5% |

Kill the sequence and rewrite if open rate is under 30% after 500 sends or unsub is over 1%.

---

## Forbidden moves

- No "just following up"
- No "did you see my last email"
- No fake urgency ("limited beta seats")
- No forwarded-chain fakery ("bumping this to the top")
- No mid-sequence product launches or feature announcements — keep the narrative tight
