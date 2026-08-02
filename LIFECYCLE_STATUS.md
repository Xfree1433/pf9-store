# Lifecycle Status — what is actually wired

**Last verified: 2026-08-02** against Klaviyo (live API), `store_api.py` @ `6f94c01` (the build
running in production since the 18:19 UTC restart), and the production DB on xfree143.

Local, `origin/main`, and production are in sync. Both halves of the day-27 fix are live: the
Klaviyo flow filter and the `subscription_status: 'trialing'` write. See "Day-27 filter —
2026-08-02".

✅ **The `events:write` blocker is CLEARED (2026-08-02, later the same day).** A new private key
with Events + Lists + Profiles access replaced the old Lists+Profiles-only one; Klaviyo does not
allow editing an existing key's scopes, so the old key was replaced rather than amended. All three
metrics — `Started Checkout`, `Placed Order`, `Cancelled Subscription` — now exist in the account
and are selectable as flow triggers. **L2, L6 and L7 are no longer blocked on scope; they are now
blocked only on flow-building**, which is ordinary work. Scope probe after the swap:
`profiles` / `metrics` / `lists` / `flows` all **200**, `POST /api/events/` **202**.

`PLAYBOOK_LIFECYCLE.md` is the *spec* — what the sequences should say and why. It deliberately
carries no implementation state, because a spec that also tracks build status stops being
readable as either. This file is the other half: for each specced sequence, what exists in
Klaviyo and in code right now.

**Rule for this file: only record what was observed, and say how it was observed.** Anything
inferred rather than read is marked. Anything unchecked is marked UNKNOWN rather than assumed
absent — "I didn't look" and "it isn't there" are different facts and collapsing them is how a
status doc starts lying.

---

## Stack — decided

`PLAYBOOK_LIFECYCLE.md` line 3 still reads *"marketing via ESP (Customer.io / Loops / Resend —
Cowork picks in week 2)"*. That is stale. The decision was made and built:

| Layer | Actual |
|---|---|
| Marketing / lifecycle email | **Klaviyo** — flows live since 2026-05-30 |
| Transactional (welcome, password, alerts) | `store_api.py` SMTP path, unchanged |
| CRM | HubSpot — `HUBSPOT_TOKEN` set, contacts pushed on demo-request and checkout |
| Profile sync | `_klaviyo_sync()` in `store_api.py`, fail-soft, never blocks a request |

`KLAVIYO_API_KEY` is set and present in the running `pf9-store-api` process, so profile sync is
**active**, not dormant. `KLAVIYO_LIST_TRIAL` / `KLAVIYO_LIST_PAID` / `KLAVIYO_REVISION` are NOT
in the env — the code defaults are what run. Both default list IDs were confirmed real:

| Constant | Default in code | Klaviyo list name |
|---|---|---|
| `KLAVIYO_LIST_TRIAL` | `RKeAnZ` | Trial Users — Active |
| `KLAVIYO_LIST_PAID` | `SfBnvH` | Paid Subscribers |

---

## Flows that exist in Klaviyo

**Two. That is the whole set** — the account was listed in full, not filtered.

### `X2tesT` — PF9 Trial Onboarding · live · trigger: Added to List

Order confirmed by walking each action's explicit `next` pointer, not inferred from ID order:

```
email (day 0) → wait 3d → email (day 3) → wait 24d → email (day 27)
```

Day 27 is the pre-charge notice, on a 30-day trial (`TRIAL_PERIOD_DAYS=30`). This confirms the
claim in `store_api.py`'s header comment that Klaviyo — not the app — owns that email. The app
deliberately has no day-27 sender; `_send_trial_ending_email` was removed precisely so the two
could not both fire.

**Filtering:** as of 2026-08-02 this flow carries a `profile_filter` that drops anyone whose
`subscription_status` is `cancelled`, so a cancelled trial no longer receives the day-27 charge
notice. `additional_filters` remains `null` on all three messages — the guard is flow-level by
design, so it covers any message added later. See "Day-27 filter — 2026-08-02".

### `VuD82q` — PF9 Paid Onboarding · live · trigger: Added to List

```
wait 30d → email (day 30) → wait 60d → split → Path #1  → email (day 90)
                                             → Everyone else → End
```

The day-90 email is **L5-E1, the month-3 expansion pitch, and it is live and sending today.**
Since 2026-08-02 it sits behind a conditional split on `app_count` — see "L5 — closed 2026-08-02".

---

## Sequence map — spec vs. built

| # | Spec | Built? | Detail |
|---|---|---|---|
| L1 | Video viewer, no subscribe | **No flow** | Needs a `video_play` event. Nothing in `store_api.py` emits one; no flow exists to consume it. |
| L2 | Cart abandon | **Not built — unblocked, flow work remains** | `create_checkout_session()` emits `Started Checkout` and conversion emits `Placed Order`. Both deployed 2026-08-02, and both metrics now exist in Klaviyo (scope fixed same day), so they are selectable as trigger and exit condition. The flow itself is still unbuilt. See "Three things that will bite whoever builds the flow". |
| L3 | New subscriber onboarding | **Partial; day-27 defect closed** | Trial flow (3 emails @ 0/3/27) + Paid flow both live. Spec says 4 emails over 14 days; actual trial cadence is 0/3/27 — still unresolved. **The day-27 defect is fixed:** a profile filter on `X2tesT` now drops cancelled trials before the charge notice. See "Day-27 filter — 2026-08-02". |
| L4 | Month-1 success | **Live** | Day-30 email in the Paid flow. Whether its content matches the spec's testimonial ask was NOT checked. |
| L5 | Month-3 expansion | **Live + conditional** | Day-90 email in the Paid flow, gated on `app_count` since 2026-08-02. See below. |
| L6 | Churn-save | **Not built — unblocked, flow work remains** | Cancel emits `Cancelled Subscription`, deployed, and the metric now exists (scope fixed 2026-08-02), so L6-E1 (the 24h email) is buildable. The L6 *intercept page* is frontend code and is still not started. |
| L7 | Win-back | **Not built — L7-E2 unblocked, L7-E1 still blocked on data** | Same trigger as L6, and the scope block is cleared. L7-E2 is now buildable, but **L7-E1 is not** — its copy merges `{{reason}}` and `{{change}}`, and nothing collects either. That is a data gap, not a permissions one. See "L6 / L7 — 2026-08-02". |

---

## Day-27 filter — 2026-08-02

**Finding: a customer who cancels their trial still receives the day-27 "your card is charged on
[date]" email. The protection the code claimed to provide does not exist.**

`_handle_subscription_cancelled()` removes the profile from `RKeAnZ` (Trial Users — Active) and
its comment claimed this "stops a day-27 notice about a charge that will never happen." It does
not. Removal stops them *entering* the flow. It does not pull them out of one they are already
in — and day 27 sits behind a 24-day delay, so anyone who cancels after day 3 is already in it.

### What was checked (state *before* the fix — kept as the evidence for the finding)

| Where | What it says |
|---|---|
| API — flow `X2tesT` | `profile_filter: null` |
| API — messages `VpT7Fy`, `YpvAcX`, `ReYNde` | `additional_filters: null` on all three |
| UI — Trigger card | Trigger: Added to list, Trial Users — Active. Re-entry: none. **"No profile filters applied."** |
| UI — Day 27 card → Settings | **Additional filters: empty**, "Add filter" untouched |

The message that lands (`ReYNde`, template `TGNJvL`), verbatim:

- Subject: `Your {{ person.Properties.app_name|default:'PF9' }} trial ends {{ person.Properties.trial_end_date|default:'soon' }}`
- Preview: `Your card is charged on that date. Cancel any time before then.`

So the customer who already cancelled is told their card is about to be charged, and invited to
cancel something they have already cancelled. This is not a merely-irrelevant email; it reads as a
billing error and invites a support ticket.

### Why removal alone is not enough

Klaviyo re-checks **profile filters** before each message and skips anyone who fails; **trigger
filters are not checked again at send time**. This flow has neither. The "must still be a member
at send time" guarantee that people assume covers this is documented for **segments**, not lists
— and this is a list-triggered flow. Klaviyo's own docs are silent on list removal mid-flow, and
the community answer to exactly this problem is to add a flow-level profile filter, which "kicks
them out before the next step" if they are sitting in a delay.

Relying on undocumented behaviour is a bad trade here. The failure mode is a customer being told
their card is about to be charged after they cancelled — the one email where being wrong costs a
support ticket and trust, not a click.

### The fix — APPLIED 2026-08-02 18:02 UTC

A **flow-level profile filter** now sits on `X2tesT`. Flow-level, not per-message, so it also
covers anything added to this flow later. As stored:

```json
"profile_filter": {"condition_groups": [{"conditions": [
  {"property": "properties['subscription_status']",
   "filter": {"type": "string",    "operator": "not-equals", "value": "cancelled"}},
  {"property": "properties['subscription_status']",
   "filter": {"type": "existence", "operator": "not-set"}}
]}]}
```

Both conditions live in **one** `condition_group`, which is Klaviyo's OR. Reads as: *not cancelled,
**or** never set.*

**Why the OR matters.** The obvious one-line filter — `subscription_status is not equal to
cancelled` — is a trap. Klaviyo's handling of a *missing* property under a negative operator is not
documented, and every profile created before today lacks the property entirely: a custom property
does not exist in the account, or in the flow-editor's Dimension picker, until something writes it.
Had "missing" evaluated as *fails*, the filter would have silently suppressed the entire trial
sequence for every pre-existing profile — trading a wrong email for no emails at all. The
`is not set` branch removes the guess.

**Verified after saving**, via `get_flow`, that the filter persisted *and* that the action chain was
not disturbed — the incident below is why this is checked rather than assumed:

```
107907408 (Day 1) → 107907493 (3d) → 107907514 (Day 3) → 107907598 (24d) → 107908224 (Day 27) → null
```

All five actions still report `updated: 17:41:48` while the flow moved to `18:02:30`, so the save
touched the filter and nothing else.

**Data side.** `store_api.py` already wrote `subscription_status = 'cancelled'` on the last-app
cancel path — only when the customer's **last** app goes, which is correct here: someone cancelling
one app of two is still trialing the other and should still get its notice. What was missing is that
nothing ever wrote the property back *up*. `_handle_subscription_updated` only writes `'active'` at
conversion, three weeks later, so a returning customer would sit at `'cancelled'` through their
entire second trial. The trial-start sync now writes `subscription_status: 'trialing'`.

To be precise about what that reset does and does not buy: it does **not** currently rescue a
returning customer's welcome email, because `X2tesT` is set to **No re-entry** (confirmed 2026-08-02
— `reentry_criteria` is absent from the flow definition), so they never re-enter the flow for the
filter to judge them. It is worth writing anyway because `'cancelled'` on someone who is actively
trialing is simply false, and the filter has now made this property load-bearing: any flow or
segment keyed on it inherits the lie, and turning re-entry on later would convert it into a silent
suppression of the whole onboarding sequence.

**Deployed 2026-08-02 18:19 UTC** (`6f94c01`, MainPID 3799585). Both halves are now live. The
restart was verified the only way that proves anything with gunicorn — the new process start
(18:19:12) is later than `store_api.py`'s mtime (18:08:02), so the workers actually imported this
build rather than continuing to serve the previous one behind a 200 on `/health`. The deploy also
confirmed `KLAVIYO_API_KEY` is present, so the `subscription_status` writes genuinely reach
Klaviyo — without that key the filter would be judging a property nothing ever sets.

**Blast radius at the time of the fix:** the Klaviyo account holds 3 profiles, all test data. The
defect was real, and is now closed, but it had reached no real customer.

### Incident note

While inspecting the canvas, a click-drag intended to pan the view instead moved the
"Trial Day 3 — Check-in" node below the day-27 node. Klaviyo persists structural edits to live
flows immediately — the API confirmed the reordered `next` chain. It was dragged back and the API
re-read confirms the original order restored exactly:

```
107907408 (Day 1) → 107907493 (3d) → 107907514 (Day 3) → 107907598 (24d) → 107908224 (Day 27) → null
```

Wrong for ~3 minutes. The flow shows no sends in the last 30 days, so nothing was mis-sent. Pan
the canvas from empty space only — anywhere over a node is a node drag.

---

## L6 / L7 — 2026-08-02

These were on the backlog as "flow-building, no code — the cancellation data already syncs." That
was wrong, and the reason is worth keeping:

**Writing a profile property does not start a Klaviyo flow.** Flows trigger on a list join, a
segment join, or a metric — nothing else. The cancel handler wrote `subscription_status: cancelled`
and removed the profile from the trial list, so the *data* was correct and completely inert. There
are also zero segments in the account, so there was no segment to join either. `3a88fe7` adds a
`Cancelled Subscription` event.

| Property on the event | Why it's there |
|---|---|
| `app_name` / `product` | The app actually cancelled |
| `remaining_app_count` | `> 0` ⇒ still a customer, must not get win-back copy |
| `reactivate_link` | Storefront card for that app; never expires |
| `unique_id` | Subscription id, so a redelivered webhook records one cancellation |

### The defect this uncovered

The old handler flagged the profile cancelled **unconditionally**. A customer with two apps who
cancelled one was marked churned account-wide and pulled off the trial list. Consequences, none of
which anyone would have noticed until L6/L7 went live:

- a still-paying customer would receive "saw you canceled" and win-back copy;
- if their *other* app was mid-trial, removal from the trial list would have killed its day-27
  pre-charge notice — a customer charged without warning;
- `app_name` carried whatever the last checkout wrote, so the "you closed your ___" subject line
  could name the app they kept.

Cancellation is now evaluated against `_owned_apps()` *after* the status update, and only a customer
with nothing left is flagged, delisted from both lists, and treated as churned.

`app_count` is refreshed here too. It was previously only recomputed on the way up, so someone who
dropped from two apps to one kept a stale count of 2 — which the L5 split reads as "already
expanded" and silently suppresses the month-3 pitch. That was a live bug against the split shipped
earlier the same day.

### What is still blocked

**L7-E1 cannot be built as written.** Its body is "you mentioned `{{reason}}`. Since then:
`{{change}}`." Neither exists:

- `reason` comes from the L6 intercept page, which is frontend code and does not exist;
- `change` has no source at all — it is a per-customer claim someone has to author.

Building it anyway renders "you mentioned ." to every recipient. Either write the intercept page
first, or rewrite L7-E1 generically. This is a decision, not a task.

**The `Cancelled Subscription` metric now exists** (created 2026-08-02 by the bootstrapper, after
the key scope was fixed), so the chicken-and-egg that blocked both L6 and L7 is gone and the flow
editor will offer it as a trigger. What remains blocking L7-E1 is the missing `reason` / `change`
data above, which no amount of Klaviyo configuration solves.

**Consent.** A churned customer is still a contactable profile, but check their consent state before
assuming L7 will deliver; Klaviyo silently skips non-consented profiles.

---

## L2 — half-closed 2026-08-02

`7f83a91` shipped the missing data and it is now deployed (2026-08-02, service restarted onto
`fb501d8`). It did **not** build the flow.

| Metric | Emitted from | Carries |
|---|---|---|
| `Started Checkout` | `create_checkout_session()`, after `Session.create()` succeeds | `app_name`, `resume_link`, `restart_link`, `unique_id` = Stripe session id |
| `Placed Order` | `_handle_checkout_completed()` | `app_name`, `value` (dollars), `unique_id` = subscription id |

`Placed Order` is not decoration. The flow's exit condition is "has not placed an order since
starting", so without it every customer who *did* buy still gets the "you didn't finish" email an
hour later.

Both are emitted **per checkout, not per person**, so an existing customer buying a second app both
enters and exits correctly. Filtering on trial-list membership instead would read them as
already-converted and never mail them at all.

### Three things that will bite whoever builds the flow

**✅ RESOLVED 2026-08-02 — the API key could not write events at all, which blocked L2, L6 and L7
outright.** Kept here because both failure modes are silent and will recur on any future key.

The original symptom, from calling the deployed `_klaviyo_event` directly against production:

```
403 permission_denied
"Your API key is missing required scopes: events:write"
```

Scope probe on that key: `GET /api/profiles/` → **200**, `GET /api/metrics/` → **403**, and
`GET /api/flows/` → **403** as well (not probed the first time). The key was provisioned for
profiles and lists only. That split explains a discrepancy that otherwise looks like a code bug:
profiles carried correct `subscription_status` values while not one PF9 metric existed. The profile
half was always working; the event half had never worked once.

It failed **silently, by design** — `_klaviyo_event` is fail-soft (its docstring: a Klaviyo outage
must cost a lifecycle email, never a sale), so every call ended at a `print` on the store host.
Nothing alerts. The restart script made it worse by reporting `KLAVIYO_API_KEY present — Klaviyo
sync will be ACTIVE`, conflating presence with authorisation; that message has been corrected.

**How it was fixed.** Klaviyo has no way to edit an existing key's scopes — the ⋮ menu offers only
Disable / Clone / Delete — so the key had to be **replaced**, not amended. A new private key with
Full Access on Events, Lists and Profiles was issued and written to
`/opt/pf9-store/pf9-store-api.env`, followed by a `pf9-store-api.service` restart. That file had
been carrying `KLAVIYO_API_KEY` on **two consecutive byte-identical lines**; the duplicate was
deleted at the same time, since a later assignment silently wins and would have defeated a
single-line edit.

**⚠️ Second silent failure, found immediately after.** With the correct scope the first bootstrap
run still produced no metrics — every event returned **`202 Accepted`** and was then discarded.
Cause: the events were attached to `test@example.com`, and Klaviyo drops profiles on RFC-2606
reserved domains *after* accepting the request. Re-firing the identical payloads against
`metric-bootstrap@plainspokenfoundrynine.com` created all three metrics. `tools/pf9_metric_bootstrap.py`
now hardcodes an owned domain and documents why.

**The lesson worth keeping: neither `202` nor "no exception" means an event landed.** The metric
list is the only proof. Verify with `GET /api/metrics/` after every change.

**All three metrics now exist** — `Started Checkout`, `Placed Order`, `Cancelled Subscription` —
so the flow editor's trigger picker lists them and L2 / L6 / L7 are buildable. The account went
from 22 metrics (all Klaviyo-internal but `Active on Site`) to 25. Note that Klaviyo metrics
**cannot be deleted**, so these names are now permanent; they were verified character-for-character
against the three production call sites in `store_api.py` before sending.

A ready-to-run bootstrapper is committed at `tools/pf9_metric_bootstrap.py` (dry-run by default,
`fire` to send; run it on xfree143 with `/opt/pf9-store/venv/bin/python`, which is where the key
and the deployed module are). It calls the **deployed** `_klaviyo_event` rather than a hand-rolled POST,
so the permanent metric names come from the code that will emit them, and it mirrors each real call
site's properties so Klaviyo learns the property names for the flow editor's picker. It will work
unchanged once the scope is granted.

**`resume_link` dies before L2-E2 does.** Stripe expires checkout sessions after 24 hours; the spec
sends E2 at 48. The event therefore carries two links, and they are not interchangeable:

- `resume_link` — Stripe's hosted page, keeps the exact cart, **valid ~24h**. Use in E1 (1 hour).
- `restart_link` — the storefront card (`/?product=X`), never expires, costs the customer a
  re-typed name and email. Use in E2 (48 hours).

Using `resume_link` in E2 ships a link that renders an expired-session error to every recipient.

**The event upserts a profile but does not grant marketing consent.** That is deliberate — a person
who typed their email into a checkout form has not subscribed to anything, and deciding otherwise is
a consent call, not a code call. Klaviyo will skip flow sends to a non-consented profile unless the
message is configured to allow it, so this has to be settled *before* the flow goes live or L2 will
appear to work and silently deliver nothing.

### Verifying after deploy

```bash
# 1. did the metrics appear?
#    Klaviyo MCP: get_metrics fields_metric=["name","integration"]
#    Expect "Started Checkout" and "Placed Order", both integration.category = API.
#    If they are absent after a real checkout, the deploy did not take.

# 2. is the pair balancing?
#    A healthy week has Started Checkout >= Placed Order. If they are equal,
#    nothing is abandoning, which almost certainly means the start event is
#    firing late rather than that the store converts at 100%.
```

Failures are logged, never raised — `[Store API] Klaviyo event "Started Checkout" ...` on the store
API journal is the only place a broken send shows up. A silent absence of that line means
`KLAVIYO_API_KEY` is unset, not that everything is fine.

---

## L5 — closed 2026-08-02

The day-90 expansion email is live and **now gated on a conditional split**, so a subscriber who
already owns more than one app is no longer pitched an app. Before 2026-08-02 the Paid flow held
only `send-email` and `time-delay` actions — no profile filter, no branch — and every paid
subscriber reaching day 90 got the pitch unconditionally.

`b4d80e0` shipped the data the split reads:

| Property | Set where | Purpose |
|---|---|---|
| `app_count` | checkout completed; trialing→active | Integer the split reads. `>= 2` ⇒ skip the pitch. |
| `apps_owned` | same | Comma-separated names. Exists so a human opening the profile can audit *why* `app_count` is what it is. |
| `related_app_name` / `_detail` / `_url` | same | The cross-sell target the email renders. |
| `app_name`, `app_price`, `trial_end_date`, `manage_subscription_url` | checkout; trial_will_end | Trial flow merge tags. |
| `subscription_status` | cancelled; trialing→active | `cancelled` / `active`. |

Both are recomputed from the `subscriptions` table on every write, never incremented — Stripe
redelivers webhooks, and a counter would drift upward on replay.

### Why it stayed unbuilt until now

Production, read 2026-08-02:

```
subscriptions rows : 3
by status          : {active: 2, cancelled: 1}
distinct emails    : 3
customers with >1 app : 0
```

The split changes the behaviour of **zero** sends today. That was the argument for waiting. The
argument against waiting — the one that won — is that the email was already going out
unconditionally, so the gap was live rather than theoretical: the moment a second app sells, it
misfires. Building it while it is a no-op is the cheapest time to build it.

Also note: **existing profiles do not backfill.** `app_count` only lands on a profile when that
customer next hits checkout or converts trialing→active. The 3 current profiles will not have it
until then, so the split had to treat "property missing" as `0` — which is the safe direction
anyway, since 0 sends the email, i.e. today's behaviour. That is why the filter carries an `is not
set` clause and not just a numeric comparison.

### How it was built — 2026-08-02

The blocker was never UI navigation. **Klaviyo's split builder only offers dimensions it has
already observed on a profile.** Searching the Dimension picker for `app_count` returned empty,
and there is no "create custom property" affordance in that builder — a property that has never
been written cannot be referenced. The emitter was fine all along: local and server `store_api.py`
are md5-identical (`24dc663f…`), `_owned_app_properties` appears 3× in the running file, it had
simply never executed. The only rich profile (`mark.pierce@outlook.com`) was last written
2026-08-01 16:34 CDT and `b4d80e0` shipped at 20:08 CDT — exactly the no-backfill case predicted
above, not a bug.

Unblocked by writing `app_count` to one profile purely to register the dimension: the synthetic
`test@example.com` (`01KSXCGTMGDKGK70X68ASHJSH6`), which is on the Trial list only, is **not** on
the Paid list, and has `can_receive_email_marketing: false` — so it cannot reach this flow or be
emailed at all. Written as a true **integer**, which matters: an integer registers a *numeric*
dimension and so offers `is less than`; a string would have registered a text dimension with
equality operators only.

The split as built — `multi-branch-split` `113483855`, inserted between the 60-day delay
(`107907837`) and the day-90 send (`107907860`):

```
Path #1 (order 0)   app_count is less than 2  OR  app_count is not set   → 107907860 (day-90 email)
Everyone else (is_else)                                                  → End
```

Things that are easy to get backwards, all confirmed the hard way:

- **Branch placement is the inverse of the obvious guess.** Inserting a split above an existing
  action puts that action on **Path #1** (evaluated first) and auto-creates an "Everyone else"
  branch to End. So Path #1's criteria describe *who still receives* the email, not who is skipped.
- **The OR is mandatory.** In Klaviyo a numeric comparison against an absent property evaluates
  FALSE, so `< 2` alone would route every un-backfilled profile to "Everyone else" and silently
  kill the day-90 email.
- **`is not set` exists only under Type: Text.** With Type: Number the operator list is exactly
  six — equals, doesn't equal, is at least, is at most, is greater than, is less than. The
  existence operators (`is set` / `is not set`) appear only once the row's Type is switched to
  Text. So the two conditions deliberately carry different Types; that is correct, not a mistake.
- **Conditions inside one `condition_group` are OR'd, and separate groups are AND'd** — the
  inverse of the convention the Klaviyo segment docs describe. This one is worth re-checking
  before trusting any future filter, because getting it backwards yields
  `< 2 AND is not set`, which is unsatisfiable and would send the email to *nobody*. Verified by
  round-trip: the saved single group of two conditions re-renders in the UI as two rows joined by
  an `OR` chip, with Apply greyed (i.e. no pending change).
- **The canvas card lies by omission.** The Path #1 node on the canvas renders only
  "app_count is less than 2." — it truncates to the first condition. The Path details panel and
  the API both show both. Never read the canvas card as the filter.
- **Klaviyo flow edits persist server-side immediately**, even while the UI shows "Unsaved
  changes" with Save greyed out. The flow's `updated` attribute did **not** move
  (still 2026-05-30T20:07:58), so it is useless for detecting drift. Verify structure via
  `get_flows`, never via the UI or the timestamp.
- The public API is read-only for flow structure; there is no flow-mutation endpoint. This was
  UI-only work and any future change will be too.

**What to watch.** The 3 existing production profiles have no `app_count` and will not get one
until they next hit checkout or convert trialing→active. They match the `is not set` clause, so
they still receive the email — today's behaviour, unchanged. The split only begins changing
outcomes once a customer owns 2+ apps.

---

## Not verified

Listed so they are not mistaken for "checked and fine":

- **Email bodies.** Still unread — template contents (`RXA7h3`, `XtS2ji`) were never pulled, so
  whether the body copy matches `PLAYBOOK_LIFECYCLE.md` is unknown. *Partially resolved
  2026-08-02:* the **subject lines** do use `b4d80e0`'s merge tags, with defaults —
  day-30 renders `{{ person.Properties.app_name|default:'PF9' }}` and day-90 renders
  `{{ person.Properties.related_app_name|default:'another PF9 app' }}`. So the tags are wired at
  least in the subjects, and degrade safely when absent.
- **`{{current_spend}}`** (spec line 213/215). Nothing in `store_api.py` sets it. If the live
  day-90 email uses it, it renders empty or falls to a default.
- **L5-E2**, the day-100 follow-up (spec line 223). The Paid flow ends after day 90 — so it
  isn't built, but no separate flow was searched for beyond the full account list, which showed
  only two flows.
- **Flow performance.** No open/click/conversion data pulled. The 8% KPI on spec line 235 has
  never been measured.
- **HubSpot list IDs** 12/13/14 — env vars are set but the values were not confirmed against
  HubSpot.

---

## Re-verifying this file

```bash
# flows, their status, step order, AND the L5 branch_filter
#   Klaviyo MCP: get_flows filter=any(id,["VuD82q"]) include=flow-actions
#                           fields_flow_action=definition
#   Ask of the output:
#     - does action 113483855 still exist and carry a NON-null branch_filter?
#       (a null branch_filter on a live flow = undefined branching, treat as an incident)
#     - does its Path #1 still have links.next == 107907860, the day-90 send?
#     - are BOTH conditions present — numeric less-than 2 AND existence not-set?
#   Do not verify any of this from the flow editor canvas; the card truncates to
#   the first condition, and the flow's `updated` attribute never moves.
# lists
#   Klaviyo MCP: get_lists

# is Klaviyo sync actually on?
ssh xfree143.taile2beaa.ts.net \
  'P=$(systemctl show pf9-store-api.service -p MainPID --value); \
   tr \\0 \\n < /proc/$P/environ | grep -c "^KLAVIYO_API_KEY=.\+"'

# multi-app customer count
ssh xfree143.taile2beaa.ts.net "/opt/pf9-store/venv/bin/python -c \"
import sqlite3
c=sqlite3.connect('file:/opt/bridgr/store_leads.db?mode=ro',uri=True)
print(c.execute('SELECT COUNT(*) FROM (SELECT lower(email) e FROM subscriptions \
WHERE status IN (\\\"active\\\",\\\"trialing\\\") GROUP BY e HAVING COUNT(DISTINCT product)>1)').fetchone()[0])
\""
```
