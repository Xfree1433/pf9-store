# Lifecycle Status — what is actually wired

**Last verified: 2026-08-02** against Klaviyo (live API), `store_api.py` @ `92290cd`, and the
production DB on xfree143.

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
| L2 | Cart abandon | **Events shipped, flow not built** | `create_checkout_session()` now emits `Started Checkout` and conversion emits `Placed Order`. The data blocker is gone; the flow itself is still missing, and the events do not reach Klaviyo until the store API is redeployed. See "L2 — half-closed 2026-08-02". |
| L3 | New subscriber onboarding | **Partial** | Trial flow (3 emails @ 0/3/27) + Paid flow both live. Spec says 4 emails over 14 days; actual trial cadence is 0/3/27. Cadence differs from spec — spec not updated, or flow not finished. Not resolved. |
| L4 | Month-1 success | **Live** | Day-30 email in the Paid flow. Whether its content matches the spec's testimonial ask was NOT checked. |
| L5 | Month-3 expansion | **Live + conditional** | Day-90 email in the Paid flow, gated on `app_count` since 2026-08-02. See below. |
| L6 | Churn-save | **No flow** | Cancel does sync Klaviyo (`subscription_status: cancelled`, removed from trial list) so the *data* is there; no flow and no intercept page consume it. |
| L7 | Win-back | **No flow** | Same — cancellation data exists, nothing acts on it. |

---

## L2 — half-closed 2026-08-02

`7f83a91` shipped the missing data. It did **not** build the flow, and until the store API is
redeployed it changes nothing in production — the code is in git, not on the server.

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

**Neither metric exists in Klaviyo yet.** As of 2026-08-02 the account has 22 metrics and all but
`Active on Site` are Klaviyo-internal. A metric is created by its first event, and the flow editor's
trigger picker only lists metrics that already exist — so the flow **cannot be built until at least
one event has actually been received**. Order of operations is: deploy → one checkout start →
metric appears → build flow. Note also that Klaviyo metrics cannot be deleted, so the first send
fixes the name permanently.

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
