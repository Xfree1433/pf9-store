# Lifecycle Status — what is actually wired

**Last verified: 2026-08-04** against Klaviyo (live API), `store_api.py` @ `2c31dbc` (the build
running in production since the 2026-08-04 11:37:06 UTC restart, MainPID 1108356), and the production
DB on xfree143.

> ## ⛔ Read first — consent is wired now, but the programme has still delivered nothing (2026-08-04)
>
> **What changed:** as of 2026-08-04 the storefront can grant marketing consent. A customer who ticks
> the box at checkout is subscribed through `_klaviyo_subscribe`, and the key finally carries the
> `subscriptions:write` scope to make it stick. That closes the structural blocker this file spent
> two days describing.
>
> ✅ **The mechanism was proven end-to-end on 2026-08-04** — see "Consent path proven end-to-end".
> One *further* profile now reads `SUBSCRIBED`, and it is a deliberate internal test address, not a
> customer.
>
> **What did not change:** the fix is not retroactive and no *customer* has used it. No live customer
> has ticked the box, so the audience still grows only from new checkouts forward. Three flows remain
> in Draft, two are live. Treat "consent is fixed" as a statement about the mechanism, not about the
> audience — that distinction is now narrower than it was, but it is the same distinction.
>
> ⚠️ **Correction, 2026-08-04.** This callout used to say the deliverable population was "zero today".
> That was wrong when written, and the contradiction was sitting in this same file: the profile table
> under "Consent — audited 2026-08-03" lists `xfree143@gmail.com` and `mark.pierce@outlook.com` as
> **SUBSCRIBED and deliverable** since 2026-05-30. Re-read 2026-08-04 across the whole account —
> **five profiles, three deliverable**: those two plus the new `xfree143+consenttest@gmail.com`.
> `test@example.com` is SUBSCRIBED but `USER_SUPPRESSED`, and `metric-bootstrap@` is
> `NEVER_SUBSCRIBED`. All five are internal addresses, so "no customer audience" was the true claim
> and "nobody is reachable" was the overstatement. **Activating any flow sends to real inboxes today.**
>
> **The day-27 pre-charge notice is CLOSED (2026-08-04, live) — but it needs one manual step.** The
> send moved back into `_handle_trial_will_end` and now goes out on the Stripe `trial_will_end`
> webhook, which is billing infrastructure and does not consult marketing consent. The intended fix —
> flagging the Klaviyo message `transactional: true` — turned out to be **unreachable on this
> account**, for three separate reasons. See **"Day-27 pre-charge notice — moved in-house 2026-08-04"**.
>
> ✅ **Klaviyo message `ReYNde` was set to Draft on 2026-08-04**, so the store is now the only sender
> and no consented customer gets it twice. Verified by API read-back, not by the UI: action
> `107908224` reports `"status": "draft"` while Day 1 (`VpT7Fy`) and Day 3 (`YpvAcX`) remain `live`
> and the flow itself stays `live`. Chosen over Manual deliberately — Manual would have kept queueing
> recipients for a human to release, which is a different thing from not sending.

✅ **Local, `origin/main` and production are all at `2c31dbc`** (2026-08-04). The consent change went
out as two deliberately separate pushes — `b93baa2` (API) first, restart, then `73e1fef` (checkbox) —
because the two halves deploy on different clocks and shipping the checkbox first would have meant
customers ticking a box the server ignored. Both halves of the day-27 *filter* fix remain live: the
Klaviyo flow filter and the `subscription_status: 'trialing'` write. See "Day-27 filter — 2026-08-02".

✅ **The `events:write` blocker is CLEARED (2026-08-02, later the same day).** A new private key
with Events + Lists + Profiles access replaced the old Lists+Profiles-only one; Klaviyo does not
allow editing an existing key's scopes, so the old key was replaced rather than amended. All three
metrics — `Started Checkout`, `Placed Order`, `Cancelled Subscription` — now exist in the account
and are selectable as flow triggers. **L2, L6 and L7 are no longer blocked on scope, and all three
have since been built** — each is in Draft, gated on the marketing-consent question. Scope
probe after the swap:
`profiles` / `metrics` / `lists` / `flows` all **200**, `POST /api/events/` **202**.

✅ **The `subscriptions:write` blocker is CLEARED (2026-08-04)** — the same problem a second time,
for a second helper. See "Consent — shipped 2026-08-04" for the probe result and the two-attempt
detour it took to get there.

**The pattern behind both, worth naming once:** every key in this account was minted with exactly the
scopes the code needed on the day it was minted, and Klaviyo does not allow editing scopes
afterwards. So each new Klaviyo helper has cost a full key rotation, and each rotation failed
*silently* first, because every helper in `store_api.py` fails soft by design. The 2026-08-04 key is
Full Access specifically to end that cycle. If a future helper still 403s, the cause is not scope.

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

| Constant | Default in code | Klaviyo list name | Opt-in | Triggers a flow? |
|---|---|---|---|---|
| `KLAVIYO_LIST_TRIAL` | `RKeAnZ` | Trial Users — Active | single | **yes — X2tesT, live** |
| `KLAVIYO_LIST_PAID` | `SfBnvH` | Paid Subscribers | single | **yes — VuD82q, live** |
| `KLAVIYO_LIST_CONSENT` | `W7gYXU` | Marketing Consent — Storefront | single | no — deliberately |

The last column is not trivia. Adding a profile to either of the first two **starts a live onboarding
flow**, which is why the consent grant added 2026-08-03 targets a third list that triggers nothing.
`W7gYXU` was created 2026-08-03 with `single_opt_in` set explicitly — the account default is double,
and inheriting it would have made consent pending-confirmation instead of granted.

---

## Flows that exist in Klaviyo

**Five**, as of 2026-08-02 — the account was listed in full, not filtered. Two were pre-existing and
live; three (`RWvZ2m` L2, `VgquRn` L6, `RZQKa2` L7) were built on 2026-08-02 and are all in Draft,
each documented in its own section below.

⚠️ **"Live" here means the flow is switched on, not that it delivers.** All six messages across the
two live flows are `transactional: false`, and no code path grants marketing consent, so a real
customer would enter these flows and be skipped at every send. See "Consent — audited 2026-08-03".

### `X2tesT` — PF9 Trial Onboarding · live · trigger: Added to List

Order confirmed by walking each action's explicit `next` pointer, not inferred from ID order:

```
email (day 0) → wait 3d → email (day 3) → wait 24d → email (day 27)
```

Day 27 is the pre-charge notice, on a 30-day trial (`TRIAL_PERIOD_DAYS=30`).

⚠️ **No longer true as of 2026-08-04:** this used to read that Klaviyo — not the app — owned that
email, and that `_send_trial_ending_email` had been removed so the two could not both fire. The send
is now back in `_handle_trial_will_end`, which made **this Klaviyo message the duplicate**, so
`ReYNde` was **set to Draft on 2026-08-04** and no longer sends. Day 1 and Day 3 are untouched and
still Live, as is the flow. See "Day-27 pre-charge notice — moved in-house 2026-08-04".

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
| L2 | Cart abandon | **Built 2026-08-02 — in Draft, not live** | Flow `RWvZ2m` "PF9 Cart Abandon": `Started Checkout` trigger → 1h → L2-E1 (`resume_link`) → 47h → L2-E2 (`restart_link`). Both emails carry a send-time `Placed Order` = 0 filter and have Smart Sending off. Structure verified against `GET /api/flows/RWvZ2m?include=flow-actions`. **Turning it on is gated on the marketing-consent question below** — see "L2 — built 2026-08-02". |
| L3 | New subscriber onboarding | **Partial; day-27 defect closed** | Trial flow (3 emails @ 0/3/27) + Paid flow both live. Spec says 4 emails over 14 days; actual trial cadence is 0/3/27 — still unresolved. **The day-27 defect is fixed:** a profile filter on `X2tesT` now drops cancelled trials before the charge notice. See "Day-27 filter — 2026-08-02". |
| L4 | Month-1 success | **Live** | Day-30 email in the Paid flow. Whether its content matches the spec's testimonial ask was NOT checked. |
| L5 | Month-3 expansion | **Live + conditional** | Day-90 email in the Paid flow, gated on `app_count` since 2026-08-02. See below. |
| L6 | Churn-save | **Half built 2026-08-02 — L6-E1 in Draft; L6-Page not started** | Flow `VgquRn` "PF9 Churn Save": `Cancelled Subscription` trigger → 1 day → L6-E1. Send-time `Placed Order` = 0 filter, Smart Sending off. Structure verified against `GET /api/flows/VgquRn?include=flow-actions`. The L6 *intercept page* is frontend code and is still not started — it is also what blocks L7-E1. **Turning the flow on is gated on the marketing-consent question below** — see "L6 — built 2026-08-02". |
| L7 | Win-back | **Built 2026-08-02 — in Draft, not live** | Flow `RZQKa2` "PF9 Win-back": `Cancelled Subscription` trigger with a `remaining_app_count = 0` **trigger filter** → 30 days → L7-E1 → 14 days → L7-E2. Both emails carry a send-time `Placed Order` = 0 filter and have Smart Sending off. L7-E1's spec copy was unbuildable and was **rewritten generically** — see "L7 — built 2026-08-02". Structure verified against `GET /api/flows/RZQKa2`. **Turning it on is gated on the marketing-consent question below.** |

---

## Consent — audited 2026-08-03

> **Superseded 2026-08-04 as to the code, kept as the evidence for the finding.** The mechanism
> described below was fixed and deployed the next day — see "Consent — shipped 2026-08-04". Read this
> section in the past tense. One of its conclusions still holds verbatim: the fix is not retroactive,
> so no pre-existing profile gained consent from it. ⚠️ **But "the four existing profiles are still
> `NEVER_SUBSCRIBED`" — which this note used to say — was never true**, and the table immediately
> below disproves it: only `metric-bootstrap@` was. The defensible claim is the narrower one about
> retroactivity. The other conclusion — the day-27
> `transactional: false` exposure — was closed later the same day, but **not** by setting that flag,
> which proved unreachable on this account. See "Day-27 pre-charge notice — moved in-house 2026-08-04".

**Finding: nothing in the codebase ever grants marketing consent, so every profile the storefront
creates lands `NEVER_SUBSCRIBED`. This does not only gate the three Draft flows — it means the two
*live* flows have no consented audience either, including the day-27 pre-charge notice.**

This supersedes the softer "check their consent state" notes elsewhere in this file. The question is
not whether individual profiles happen to be consented; it is that no code path can produce one.

### What was checked

`GET /api/profiles` with `additional-fields[profile]=subscriptions`, full account, unfiltered —
**four profiles, all internal:**

| Profile | Consent | Deliverable | Origin |
|---|---|---|---|
| `xfree143@gmail.com` | SUBSCRIBED | yes | 2026-05-30, `subscription_status: cancelled` |
| `mark.pierce@outlook.com` | SUBSCRIBED | yes | 2026-05-30, `trialing` |
| `test@example.com` | SUBSCRIBED | **no** — `USER_SUPPRESSED` | 2026-05-30, reserved domain |
| `metric-bootstrap@plainspokenfoundrynine.com` | **NEVER_SUBSCRIBED** | no marketing | 2026-08-02, metric bootstrapper |

There is no real customer population, so this cannot be answered by sampling. It has to be answered
from the code — and the one profile created purely by current code is the unconsented one.

### Why no code path grants consent

Both Klaviyo writers in `store_api.py` avoid it, one deliberately and one incidentally:

- **`_klaviyo_event`** — deliberate, and documented in its own docstring: *"The event API upserts the
  profile as a side effect… It does NOT grant marketing consent, which is deliberate — that is a
  decision for whoever configures the flow."*
- **`_klaviyo_sync`** — incidental. It upserts via `profile-import`, then adds to a list via
  `POST /lists/{id}/relationships/profiles/`. That is Klaviyo's *add-without-subscribing* path. Only
  the subscription-create job sets consent, and it is never called.

A repo-wide grep for `subscription-create`, `subscribe_profile` and `consent` across `*.py` / `*.sh`
returns **exactly one hit** — the docstring above saying it does not happen.

**The lists do not rescue it.** `Trial Users — Active` (`RKeAnZ`) and `Paid Subscribers` (`SfBnvH`)
are both `single_opt_in`, but that governs what happens when someone *subscribes*. It does not
retroactively subscribe a profile that was only added to the list.

**The three SUBSCRIBED profiles are therefore misleading.** Their `$consent_timestamp` lands seconds
after profile creation on 2026-05-30, method `API` — hand-seeded when the account was set up, by
something that is not in this repo. They are not evidence that the product produces consented
profiles, and reading them as such is how this went unnoticed.

### The live flows are exposed too — all six messages are `transactional: false`

Read back from `GET /api/flows/{id}?additional-fields[flow]=definition`:

| Flow | Message | `transactional` | Smart Sending |
|---|---|---|---|
| `X2tesT` Trial Onboarding | Day 1 — Welcome | false | on |
| `X2tesT` Trial Onboarding | Day 3 — Check-in | false | on |
| `X2tesT` Trial Onboarding | **Day 27 — Pre-Charge Notice** | **false** | off |
| `VuD82q` Paid Onboarding | Month 1 — Check-in | false | on |
| `VuD82q` Paid Onboarding | Month 3 — Expansion | false | on |

*Still the live Klaviyo config as read — none of these **flags** changed. What changed is that the
day-27 row no longer matters for delivery: that notice is sent by `store_api.py` now, and the
message (`ReYNde`) was set to **Draft** on 2026-08-04, so it does not send at all. Its
`transactional: false` is recorded above as found, not as something still in effect. The other four
are unaffected and still Live.*

Four of those are marketing and correctly flagged. **The day-27 notice is not marketing** — its
preview text is "Your card is charged on that date. Cancel any time before then." It is a billing
notification carrying a marketing flag.

### ✅ RESOLVED 2026-08-04 — the day-27 notice had no fallback

**Kept as the evidence for the finding; the state below is no longer current.** The resolution is not
the one proposed in "Two fixes" — see "Day-27 pre-charge notice — moved in-house 2026-08-04".

`store_api.py` line 87 stated it *at the time*: *"Klaviyo owns the day-27 pre-charge notice, which is
why `_handle_trial_will_end` no longer emails directly."* The in-app sender had been removed on
purpose so the two could not double-fire. So for a real customer under that code:

1. Trial starts → `_klaviyo_sync` adds them to `RKeAnZ` without consent → `NEVER_SUBSCRIBED`
2. Day 27 → flow is live, profile filter passes, Smart Sending already off on this message
3. Klaviyo skips the send for lack of consent
4. Nothing else sends — **the card is charged with no warning**

That is a billing-surprise and chargeback exposure, not a missed marketing touch. It is also the
hardest kind to notice, because the flow reports as live and healthy throughout. Note this is a
*second, independent* way the day-27 email fails, stacked on the cancelled-trial defect recorded in
"Day-27 filter — 2026-08-02" below. That one was fixed; this one is open.

### Two fixes, deliberately kept separate

1. **Flag day-27 `transactional: true`** — believed at the time to be one setting in the Klaviyo UI,
   no code. Defensible on the merits: a pre-charge billing notice genuinely is transactional, which is
   the same reasoning that already turned Smart Sending off on that message alone. **❌ This turned out
   to be impossible on this account — the setting does not exist here. See the next-but-one section
   for the three gates. The billing exposure was closed in code instead.**
2. **Add a consent step at checkout** — the real fix, and a code change. Unblocks L2/L6/L7 and makes
   the other four live emails legitimate rather than dormant. **Built 2026-08-03 — see the next
   section. Committed, not yet deployed, and inert until the API key gains a scope it lacks today.**

**Do not generalise fix 1.** Flagging the win-back, expansion or cart-abandon emails transactional to
route around consent is the abuse pattern that flag exists to prevent. It applies to the pre-charge
notice and nothing else in this file.

**Not verified:** no live send test was run, so "Klaviyo skips non-consented profiles" is Klaviyo's
documented behaviour applied to observed config, not something watched happening. A single real send
to a `NEVER_SUBSCRIBED` profile would settle it. Note also that `metric-bootstrap@` reports
`can_receive_email_marketing: true` *while* `NEVER_SUBSCRIBED` — that field tracks suppression and
deliverability, not consent, and is not evidence the send would land.

---

## Day-27 pre-charge notice — moved in-house 2026-08-04 (live in production)

Closes the exposure recorded two sections above. **The fix is not the one that section proposed.**

### Why `transactional: true` was never available

Three independent gates, each sufficient on its own to block it. Established by exhausting five UI
locations, searching the page accessibility tree, then confirming against Klaviyo's own
documentation (article `360003165732`) and a live API re-read:

| Gate | Requirement | This account | How observed |
|---|---|---|---|
| Plan | Paid plan | **Free** | Klaviyo billing UI |
| Trigger | Metric-triggered flow only | `X2tesT` is `trigger_type: "Added to List"` | `GET /api/flows/X2tesT` |
| Mode | Message must be in Manual mode | Day 27 is **Live** | flow definition |

And clearing all three would only earn the right to *apply*: Klaviyo reviews the request (~24h), and
any later content edit strips the designation. That is not a dependency a billing notice should have.

**Stripe's built-in trial-ending email is not a substitute either.** It fires **7 days** before trial
end — day 23 of a 30-day trial — not 3. Three different clocks are in play and they are easy to
conflate: Stripe's built-in reminder (day 23), the `customer.subscription.trial_will_end` webhook
(day 27), and the Klaviyo flow's day-27 step (27 days after *list add*, not after trial start).

*Not observed:* whether that Stripe email is currently enabled. The setting is dashboard-only —
`GET /v1/account` returns no `billing` block (`settings` carries `bacs_debit_payments, branding,
card_issuing, card_payments, dashboard, invoices, payments, payouts, sepa_debit_payments`). Reading it
needs a dashboard login. Enabling it would be *additive*, not a replacement.

### What the code does now

`_handle_trial_will_end` sends directly via Resend (`_send_trial_ending_email`), on the Stripe
`customer.subscription.trial_will_end` webhook. Copy is ported verbatim from Klaviyo template
`TGNJvL`, so the wording customers get is the wording that was written and reviewed — only the
delivery path changed. Price and billing date are read **off the Stripe subscription object**, not
from stored profile properties, so the email cannot quote a figure that differs from the invoice.

Guards, each there for a specific failure:

- **Cancellation** is read from `cancel_at_period_end` / `canceled_at` on the webhook payload, *not*
  from our `status` column. A portal cancellation during trial arrives as
  `customer.subscription.updated`, and `_handle_subscription_updated` writes only `status` and
  `trial_end` — so `cancel_at_period_end` is never persisted and local status stays `trialing`. A
  DB-only check would have told a cancelling customer their card was about to be charged.
- **Refuses to send** if it cannot name both the amount and the date; alerts `NOTIFY_EMAIL` instead.
  A notice reading "charged $None" is worse than silence.
- **Idempotency** via an atomic `UPDATE … WHERE` claim checked on `rowcount` — Stripe retries on any
  non-2xx and gunicorn runs 2 workers. The claim column `trial_notice_sent_for` holds *the `trial_end`
  the notice was sent for*, not a timestamp, so a retry for the same date is suppressed while an
  extended trial re-arms.
- **A failed send releases the claim**, so Stripe's retry gets a real second attempt. For a billing
  warning a possible duplicate is the better failure than a possible silence.

Verified by execution, not inspection: 13 behavioural groups against a real temp SQLite DB with only
the two outbound edges stubbed, plus a migration test against a copy of the live table shape. All pass.

### Three defects found by auditing the diff, not by tests

All three were in newly written code and all three passed a green suite:

1. **False charge notice to a cancelling customer** — the `cancel_at_period_end` case above.
   Customer-facing billing error; no test would have surfaced it.
2. **Extended trial swallowed** — a bare "sent" flag suppressed a legitimate second notice. Fixed by
   claiming on the date rather than on a boolean.
3. **Subject-line over-escaping** — HTML-escaping a plain-text subject renders a literal `&amp;` in
   the inbox. Split escaped body label from raw subject label.

### Deploy record

| | |
|---|---|
| Commits | `b11797e` (the move), `2c31dbc` (migration race + restart-script guards) |
| Restart | 2026-08-04 11:37:06 UTC, MainPID `637400` → `1108356` |
| Migration | `trial_notice_sent_for` added to `subscriptions`; 14 columns, no duplicates |
| Health | 200 direct `:5011`, 200 via nginx, 401 `/subscription-status` |

**The migration race was not hypothetical.** `init_db()` runs at import in `wsgi_store.py`
(server-only, *not in this repo*) and gunicorn starts 2 workers without `--preload`, so both workers
read the same `PRAGMA` and both attempted the `ALTER`. The journal for this restart shows it firing:

```
[Store API] Column trial_notice_sent_for already added by another worker
```

Without the duplicate-column tolerance added in `2c31dbc`, that worker would have died at boot — on a
restart that had just reported success. **Any future column follows the same path; use `add_column`.**

`restart_store_api.sh` also had to be corrected: its verify block asserted `_send_trial_ending_email`
was **absent** (written when Klaviyo owned the send), which would have aborted every restart. The
sense is now inverted. `EXPECT_MD5` is hand-maintained and must be bumped on every `store_api.py`
change — `62d03e9b…` for `b11797e`, `6628991d…` for `2c31dbc`.

### ✅ Done 2026-08-04 — exactly one of the two is sending

The invariant is that exactly one sender is live at a time. Both ways of breaking it are silent:

| | |
|---|---|
| `ReYNde` **Live** + current code | consented customers get the notice **twice** |
| `ReYNde` **Draft** + rolled-back code | **nobody** is warned before their card is charged, silently |

**Klaviyo message `ReYNde` was set to Draft on 2026-08-04** (flow `X2tesT`, send-email action
`107908224`), leaving the store as the only sender. This is UI-only — the public API exposes flow
messages read-only, so it could not be scripted, and `restart_store_api.sh` cannot assert it either.
Confirmed afterwards by reading the flow definition back through the API rather than trusting the
editor: action `107908224` reports `"status": "draft"`, while Day 1 (`VpT7Fy`) and Day 3 (`YpvAcX`)
still report `"live"` and the flow itself is still `live`.

Draft rather than Manual, deliberately: Manual keeps queueing recipients for a human to release,
which is not the same as not sending.

**The pairing rule still applies to rollback.** If the code is ever rolled back, switch `ReYNde` back
to Live *as part of* the rollback, not after; the rollback notes at the foot of `restart_store_api.sh`
spell this out.

Note what `ReYNde` alone cannot do, which is the whole reason the code moved: it is
marketing-classified, so it only ever reaches profiles with marketing consent. Customers who declined
the checkout tick are unreachable that way.

### Infrastructure coupling discovered en route

`pf9-store-api.service` carries **two** `EnvironmentFile=` lines — `/opt/bridgr/.env` (which holds
`STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET`) and `/opt/pf9-store/pf9-store-api.env`. The store DB
is also `STORE_DB_PATH=/opt/bridgr/store_leads.db`.

**The store's secrets and its database both live inside legacy BRIDGR.** That is undocumented
elsewhere and matters because BRIDGR-on-xfree143 is otherwise treated as read-only legacy: a BRIDGR
cleanup that removed `/opt/bridgr` would take the store's Stripe keys and every subscription record
with it.

### Blast radius at time of change

3 rows in `subscriptions`, all test data (Mar/Apr 2026), all `trial_end` NULL. **No customer has ever
run the trial flow**, so the exposure this closed was prospective, not active.

---

## Consent — shipped 2026-08-04 (live in production)

Fix 2 above. Built 2026-08-03, deployed 2026-08-04 in two ordered pushes. Live and functional; see
the "Read first" callout for why *live* still does not mean *anyone has received anything*.

| | | |
|---|---|---|
| `b93baa2` | API side — `_klaviyo_subscribe`, `KLAVIYO_LIST_CONSENT`, restart-script guards | pushed, restarted 01:25:48 UTC |
| `73e1fef` | Storefront side — the checkbox in the subscribe modal | pushed, Pages run `30868771729` success |

Verified live after deploy: `store.plainspokenfoundrynine.com` returns 200 and serves
`id="subConsent"` with **no** `checked` and **no** `required` attribute; the API rejects a probe at
product validation rather than at required-fields, so it parses a body containing `marketing_consent`;
`MainPID 637400` started `01:25:48 UTC` against code written `01:22:02 UTC`.

### What the code does

- **`_klaviyo_subscribe(email, list_id)`** — `POST /api/profile-subscription-bulk-create-jobs/`,
  setting `subscriptions.email.marketing.consent = SUBSCRIBED`, tagged
  `custom_source: 'Storefront checkout'` so the consent record carries its own provenance.
- **`create_checkout_session`** reads `marketing_consent` from the request body. It is *not* in the
  required-field check — a tick you cannot check out without is not consent.
- The call sits **after `_klaviyo_event` and outside the `try`**, per the existing comment at the
  top of that region, so a Klaviyo failure can never be reported to the customer as
  "Failed to create checkout session".
- **Checkbox is unticked by default and not `required`.** A pre-ticked box is not affirmative
  consent. Its wording separates marketing from billing email, so declining does not read as opting
  out of the day-27 notice. **As of 2026-08-04 that separation is real rather than just promised:**
  the day-27 notice is sent by the webhook handler and never consults consent, so a customer who
  declines still gets warned before their card is charged.

### Three decisions worth not re-litigating

**Granted at checkout *start*, not in the webhook.** Checkout start is the only moment that covers
someone who abandons — and abandoners are precisely who L2 exists to reach. A webhook-time grant
would reach only customers who completed, i.e. the ones who need it least.

**Subscribes to a dedicated list, `W7gYXU` "Marketing Consent — Storefront".** Created 2026-08-03,
single opt-in, no flow triggers, used for nothing else. It is *not* either lifecycle list, and this
is load-bearing: `RKeAnZ` triggers **X2tesT (live)** and `SfBnvH` triggers **VuD82q (live)**, both on
`Added to List`. Subscribing to either at checkout start would begin trial onboarding for someone who
has not paid and may never. Verified via
`GET /api/lists?include=flow-triggers`.

**The list relationship is required, not optional.** Omit it and Klaviyo falls back to the
**account-level default opt-in process, which is Double opt-in** (Settings → API keys → Default
opt-in settings, read 2026-08-03). The profile would then sit unconfirmed pending a click while
`_klaviyo_subscribe` saw its 202 and reported success. Consent itself is profile-level rather than
list-level, so this one grant is what makes *every* flow deliverable to that person, not just flows
reading `W7gYXU`.

### The scope block, and how it was cleared

The code shipped inert on 2026-08-03 because the key lacked `subscriptions:write`. Probed against the
key then in `/opt/pf9-store/pf9-store-api.env`:

| Endpoint | 2026-08-03 | 2026-08-04 |
|---|---|---|
| `GET /api/lists/` (control) | **200** — key valid | **200** |
| `POST /api/events/` | **400** — `events:write` present | **400** |
| `POST /api/profile-subscription-bulk-create-jobs/` | **403** — `"missing required scopes: subscriptions:write"` | **400** — scope present, body rejected |

**This was the same failure shape as the events:write incident**, one day later: the helper fails soft
by design, so without the scope a customer would tick the box, see a normal checkout, and stay
`NEVER_SUBSCRIBED`. That is worse than the events gap — a silently broken promise rather than a
silently skipped email — which is why every branch of `_klaviyo_subscribe` logs.

**The detour is the part worth remembering.** Klaviyo does not allow editing scopes on an existing
private key, and the row's ⋮ menu offers only Disable / Clone / Delete. The obvious reading — clone
it and add a scope — is wrong: **Clone copies the scope set verbatim with no opportunity to change
it.** The first attempt produced a key identical to its parent, same name and same scopes, and probed
403 again. The only path with a per-scope matrix is the **"Create Private API Key"** button.

That form has its own trap: a **Custom Key starts at No Access for every scope**, so building one to
add Subscriptions will silently drop Events / List / Profiles unless all four are set — trading two
working helpers for one. The key in production is therefore a **Full Access key created 2026-08-04**,
chosen deliberately to end the rotation cycle rather than to be minimal.

**The probe is safe to repeat and should be, since any comment about scopes goes stale the moment the
key changes.** A malformed POST returns 403 for a missing scope and 400 once present, and creates
nothing either way. Note the events endpoint does **not** share that property — a valid probe there
creates a metric, and Klaviyo metrics cannot be deleted.

**Housekeeping — done 2026-08-04. Two keys remain, and the account is deliberately left with a
rollback.** The account had held five private keys, **three of them named `PF9 Store2`**, because
Clone copies the name too. The three dead ones were deleted; the listing now reads:

| Name | Created | Last used | Key ends | Standing |
|---|---|---|---|---|
| `PF9 Store2` | 08/02 | 8/3 9:32 AM | `70ee` | **kept — the rollback**, the events-scoped key that ran production until 08/04 |
| `pf9 Full access Key` | 08/04 | 8/3 8:36 PM | `5217` | **live, in `pf9-store-api.env`** |

Deleted: `pf9 store lifecycle sync` (08/01, `…b7df`, Lists+Profiles only, pre-dated `events:write`),
`PF9 Store2` (08/02, `…d6a6`, never used — a spare that never reached the env), and `PF9 Store2`
(08/04, `…78e6`, the failed clone whose only use was a scope probe).

**Identify keys by the last four characters, not the name or the dates.** Name is ambiguous by
construction, and the dates cannot be reasoned about naively — two rows read "created 08/04, last
used 8/3", i.e. used before they existed. Cause not established (a timezone difference between the
two columns is the obvious guess); what matters is that the ordering is not trustworthy on its own.
The reveal (eye) icon prints the tail,
and that is what was matched against production before anything was deleted — the live key ends
`5217`, read from `KLAVIYO_API_KEY` in `/opt/pf9-store/pf9-store-api.env`. Klaviyo's delete
confirmation says only "Delete private API key — This cannot be undone"; **it does not name the key**,
so the row must be confirmed before the menu is opened, not from the dialog.

Verified after deleting, from the server so the key never enters a transcript: the subscriptions
probe returns **400** (authenticated, scope present, creates nothing), `GET /api/profiles/` **200**,
`GET /api/metrics/` **200**. A 401 there would have meant the wrong key was deleted.

**The rollback key stays until the Full Access key has been observed working on a real checkout** —
it is the only other key carrying `events:write`.

> **That condition was met on 2026-08-04**, with one qualification: the checkout was synthetic, driven
> by a `POST` to the live endpoint rather than by a customer. It ran the identical code path and all
> three scopes were observed producing effects — profile created, **Started Checkout** event landed,
> consent stuck. See "Consent path proven end-to-end". **`…70ee` has NOT been deleted**; deleting it is
> irreversible and Klaviyo's confirmation dialog does not name the key, so that is a decision to take
> deliberately, not a loose end to tidy. Keeping it costs nothing.

### Deploy order matters — and the sequence as actually executed

`index.html` ships on push (GitHub Pages, `.github/workflows/deploy.yml`); `store_api.py` only on a
manual restart. Pushed together, there is a window where the checkbox is live against a server that
ignores the field. Hence the split, which is what was run on 2026-08-04:

1. New key into `/opt/pf9-store/pf9-store-api.env` line 5 — **replaced, not appended**; the file is
   `xfree143:xfree143 600`, so no sudo needed, and `/opt/bridgr/.env` carries no `KLAVIYO*` line to
   compete with it. The list id is baked as a code default, so this is the only env change.
2. `git push origin b93baa2:main` — API commit alone.
3. `git -C /opt/pf9-store diff HEAD origin/main` empty; restart aborts on md5 mismatch regardless
   (`EXPECT_MD5=4e2d690e869dc97e0d03cff6202a220e`, bumped in the same commit).
4. `sudo bash /opt/pf9-store/restart_store_api.sh` — interactive password, `pf9-store-api` is not on
   the NOPASSWD list.
5. Re-probe. **400 = scope landed.** Still 403 would have meant the checkbox was a lie.
6. `git push origin main` to ship the checkbox.

**How `/opt/pf9-store` actually gets its code — identified 2026-08-04.** `/opt/pf9-store-pull.sh`, a
root cron job running **every minute**:

```bash
git fetch origin main --quiet
if HEAD != origin/main: git pull --quiet && systemctl reload nginx
```

It reloads **nginx, never `pf9-store-api`.** That is the entire reason a manual restart step exists:
static files go live on their own within 60s of a push, Python never does, and the push therefore
*looks* like a complete deploy. Earlier notes in this repo said only "something root-side syncs it".

**⚠️ Incident, 2026-08-04 — a restart reported as done that never happened.** The restart was believed
complete; verification showed `MainPID` unchanged at `279263` with an `ActiveEnterTimestamp` 10 hours
older than `store_api.py`'s mtime, and the unit journal had no entry after the previous day's restart.
`/var/log/auth.log` settled it — no `sudo` invocation at all in the window. Cause: the operator was
already logged into xfree143, and the documented `ssh -t xfree143.taile2beaa.ts.net` fails there with
`Permission denied (publickey)` because the host holds no authorized_key for itself; that error
scrolled past and the sudo prompt beneath it went unanswered. **Throughout, all three health checks
returned 200 / 200 / 401.** Health proves the service is up, never which code it is running. The
decisive checks are the `MainPID` change and start-time-vs-mtime — both already in the script, and
both were what caught it.

### What this does not fix

- **The day-27 billing exposure.** Untouched *by the consent work*. ✅ Closed separately later the
  same day by moving the send into `_handle_trial_will_end`, which is exactly why it no longer depends
  on whether the box was ticked. Not fix 1 — that route proved unreachable.
- **Existing profiles.** Nothing retroactive; consent cannot be granted on someone's behalf.
- ~~**Proof.**~~ ✅ **Resolved 2026-08-04** by an end-to-end run against production. This used to read
  that `_klaviyo_subscribe` had never executed and that the probe proved only that the key *may* call
  the endpoint. It has now executed and the payload was accepted. See "Consent path proven
  end-to-end".

---

## Consent path proven end-to-end — 2026-08-04

**Ran the real path against production and read the result back out of Klaviyo.** Everything above
this section that says consent is "untested", "never executed", or "not round-tripped" was true when
written and is superseded here.

**What was run.** A single `POST` to the live
`https://app.plainspokenfoundrynine.com/store-api/create-checkout-session` carrying
`marketing_consent: true` and the address `xfree143+consenttest@gmail.com` — a plus-tagged internal
address, chosen so the resulting profile is identifiable forever and separable from any customer.
This is the production endpoint, production key, production Klaviyo account. Not a staging rehearsal
and not a direct call to `_klaviyo_subscribe`; the HTTP body was parsed by `create_checkout_session`
and the `if consent:` branch taken, which is the part that had never been exercised.

**What came back**, read with `additional-fields[profile]=subscriptions` rather than trusting the
202 — the endpoint is asynchronous and accepts before it applies:

```json
{"can_receive_email_marketing": true,
 "consent": "SUBSCRIBED",
 "consent_timestamp": "2026-08-04T12:29:35.584313+00:00",
 "last_updated": "2026-08-04T12:29:35.584313+00:00",
 "method": "API",
 "method_detail": "5217",
 "custom_method_detail": "Storefront checkout",
 "double_optin": false,
 "suppression": [],
 "list_suppressions": []}
```

`W7gYXU` went from 0 members to 1. Three events landed on the profile: **Started Checkout**,
**Subscribed to List**, **Subscribed to Email Marketing**.

**That one read settles four things at once**, which is why it was worth doing before anything else:

1. `_klaviyo_subscribe`'s payload is accepted — the schema guess for revision `2024-10-15` was right.
2. `custom_method_detail: "Storefront checkout"` proves the audit-trail string survives to the consent
   record, so a disputed subscription can actually be traced to its origin.
3. `double_optin: false` proves the explicit `single_opt_in` at list creation held. Had it fallen back
   to the account default, this profile would be sitting unconfirmed while the API reported success —
   the exact silent failure `W7gYXU` exists to prevent.
4. **`method_detail` reads `5217`, which is exactly the live key's last four.** Observed, not
   documented: no Klaviyo doc was consulted, so "Klaviyo stamps the acting key's tail onto the consent
   record" is the obvious reading of a 4-digit field matching the key in `/opt/pf9-store/pf9-store-api.env`,
   not an established fact. If it holds, it is a useful read-only way to fingerprint which key
   performed a write without ever reading the secret. Treat it as corroboration, not as the primary
   check — the tail was already matched directly against the env file before the keys were deleted.

**The three scopes are now each proven by an observed effect, not by a probe.** `profiles:write` (the
profile was created carrying the name), `events:write` (Started Checkout landed), `subscriptions:write`
(consent stuck). This is the condition the housekeeping note set for retiring the rollback key
`…70ee` — with one honest qualification: this was a synthetic checkout, not a customer's. It took the
identical code path, so the distinction is about who typed the address, not about what executed.
**Retiring `…70ee` is a deletion and is left to a decision, not done here.**

**Two things this deliberately did not prove.** A human clicking the rendered checkbox — the field was
posted directly, so the last inch of browser JS is still unobserved. And that Klaviyo *skips* a
non-consented profile, which still needs a send to a `NEVER_SUBSCRIBED` address and still sits under
"Not verified".

**Residue left behind, on purpose.** The profile stays subscribed rather than being cleaned up. It is
not the only deliverable address — see the correction in the header callout, there are three — but it
is the only one carrying a **Started Checkout** event, which is the L2 Cart Abandon trigger. That
makes it the natural canary for a first real send test, into an inbox already owned. A dead Stripe
Checkout session was also created and will expire on its own; no card, no charge.

> ⚠️ **Correction to the sentence that used to end that paragraph.** It said "turning L2 Live would
> email it". **Almost certainly wrong.** Klaviyo flows act on events received *after* activation; they
> do not backfill history, so an event from 12:29 today would not retroactively enter a flow switched
> on this afternoon. Stated as the documented behaviour, not as something observed here. It does not
> cost anything either way — firing a fresh checkout after activation takes one `curl` and gives a
> canary that definitely qualifies. Worth flagging as a trap in its own right: "the trigger event
> already exists" reads like readiness and is not.

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

**L7-E1's original copy could not be built** — resolved 2026-08-02 by rewriting it. Its spec body was
"you mentioned `{{reason}}`. Since then: `{{change}}`," and neither variable exists:

- `reason` comes from the L6 intercept page, which is frontend code and does not exist;
- `change` has no source at all — it is a per-customer claim someone has to author.

Building that verbatim would render "you mentioned ." to every recipient. The decision taken was to
**rewrite L7-E1 generically** around the two properties the event actually carries — `app_name` and
`reactivate_link` — rather than wait on the intercept page. See "L7 — built 2026-08-02".

**The L6 intercept page is still not built**, so the personalised version of L7-E1 remains
unavailable. Building it later would be an upgrade to a shipped email, not an unblocking.

**The `Cancelled Subscription` metric now exists** (created 2026-08-02 by the bootstrapper, after
the key scope was fixed), so the chicken-and-egg that blocked both L6 and L7 is gone.

**Consent.** Audited 2026-08-03 and it is worse than "check before assuming": no code path grants
consent at all, so a churned customer is addressable but not mailable. See "Consent — audited
2026-08-03" above.

---

## L6 — built 2026-08-02

**Only half of L6 was built.** The spec has two parts: L6-Page (a pre-cancel intercept asking why)
and L6-E1 (the 24-hour follow-up email). L6-E1 is built and in **Draft**. L6-Page is storefront
frontend code, does not exist, and is not a Klaviyo artifact — see "What is still blocked" above.
Its absence no longer blocks anything: L7-E1 was rewritten around properties the event already
carries, so the intercept page is now an upgrade path, not a prerequisite.

**Flow `VgquRn` — "PF9 Churn Save".** Read back from
`GET /api/flows/VgquRn?additional-fields[flow]=definition&include=flow-actions`, not from the canvas:

| Node | Action id | Value |
|---|---|---|
| Trigger | metric `REutQc` | `Cancelled Subscription`. Re-entry allowed. `trigger_filter: null`, `profile_filter: null`. |
| Delay | `113496276` | `{unit: days, value: 1, timezone: profile}`, all seven weekdays |
| Email | `113496376` | `L6-E1 - Churn save 24h`, message `SNHiyi`, template `WAn6mF` |

Email: sender `PlainSpoken Foundry Nine <support@plainspokenfoundrynine.com>`, `reply_to_email: null`
(Klaviyo routes replies to the from address — correct here, the email exists to get a reply),
subject `closed your {{ event.app_name|default:'PF9' }} — honest question`,
`smart_sending_enabled: false`, and an `additional_filters` condition on metric `XEMaYg`
(`Placed Order`), `count equals 0`, timeframe `flow-start`.

**Why the guard is a send-time filter, not a trigger filter** — same reasoning as L2: an entry-time
"hasn't re-subscribed" test passes for everyone at t=0 and never re-evaluates. On the send-email
action it is checked immediately before send, so someone who cancels and re-subscribes inside the
24-hour window is dropped rather than mailed.

**Smart Sending is deliberately off.** A cancellation follow-up suppressed because an unrelated
lifecycle email went out ten hours earlier would silently lose the one message aimed at
understanding why someone left.

**`remaining_app_count` is deliberately NOT filtered on.** That property exists to keep win-back
copy away from a still-paying customer, which is an **L7** requirement. L6-E1 asks "what would have
made it worth keeping?" about one specific app, and since the multi-app defect fix `app_name` is
accurate per-cancellation — so the question is correctly targeted even for a customer who still pays
for other apps. Adding the filter here would silence the most useful feedback in the funnel.

**Body verified at the template level**, since the canvas cannot show this: `WAn6mF` contains
`{{ person.first_name|default:'there' }}`, `{{ event.app_name|default:'PF9' }}`,
`{{ event.reactivate_link }}` and `{% unsubscribe 'Unsubscribe' %}`, and carries no residue of the
Trial Day 3 template it was cloned from. The template's auto-generated *name* still reads
`2026-08-02 20:13 PF9 — Trial Day 3: Check-in` — cosmetic only; flow-message-scoped templates cannot
be renamed via the API (PATCH `/api/templates/{id}` 404s where GET 200s), and the flow *action* name
is what appears in the editor.

**Still to do before it can go live:** the marketing-consent question below — it gates L6 exactly as
it gates L2. A churned customer who is not consented means the flow appears to run and delivers
nothing. Turning the flow on is a founder decision and was deliberately left undone.

---

## L7 — built 2026-08-02

Both emails are built and the flow is in **Draft**.

**Flow `RZQKa2` — "PF9 Win-back".** Read back from
`GET /api/flows/RZQKa2?additional-fields[flow]=definition`, not from the canvas:

| Node | Action id | Value |
|---|---|---|
| Trigger | metric `REutQc` | `Cancelled Subscription`, with a **trigger filter** `remaining_app_count equals 0`. `profile_filter: null`. |
| Delay | `113497261` | `{unit: days, value: 30, timezone: profile}`, all seven weekdays |
| Email | `113497604` | `L7-E1 - Win-back 30d`, message `WqSzAV`, template `R8kVqk` |
| Delay | `113498192` | `{unit: days, value: 14, timezone: profile}`, all seven weekdays |
| Email | `113498550` | `L7-E2 - Win-back 44d`, message `R2bqUN`, template `Rr6sCj` |

Both emails: sender `PlainSpoken Foundry Nine <support@plainspokenfoundrynine.com>`,
`smart_sending_enabled: false`, and an `additional_filters` condition on metric `XEMaYg`
(`Placed Order`), `count equals 0`, timeframe `flow-start`. Subjects are
`your {{ event.app_name|default:'PF9' }} data is still there` and
`last one — unsubscribe or keep in touch?`.

**Two different filters, for two different reasons.** This flow is the one place both kinds appear,
so the distinction is worth stating plainly:

- `remaining_app_count = 0` is a **trigger filter**, evaluated once at entry. That is correct
  *because* it is an event property — its value is frozen at the moment of cancellation and cannot
  change afterwards. A customer who cancelled one app of several never enters the flow at all,
  which is exactly the requirement: no win-back copy to someone still paying.
- `Placed Order = 0 since starting this flow` is a **send-time `additional_filters` condition on
  each email**, because its truth *does* change after entry — someone who re-subscribes on day 12
  must be dropped from the day-30 send. An entry-time version would pass for everyone at t=0 and
  never re-check. Klaviyo does not inherit these down the chain, so both emails carry their own copy.

**Smart Sending is deliberately off** on both, same as L6: a win-back suppressed because an
unrelated lifecycle email went out sixteen hours earlier would silently drop the only two messages
aimed at recovering a churned customer.

**L7-E1 was rewritten generically — a decision, not an omission.** The playbook's copy merged
`{{reason}}` (from the L6 intercept page, which does not exist) and `{{change}}` (no source at all),
and shipping it verbatim would render "you mentioned ." to every recipient. Rather than block the
flow on unbuilt frontend, E1 was rebuilt around the two properties `Cancelled Subscription` actually
carries — `app_name` and `reactivate_link` — and now says the data is still there and reactivation
is one click. The personalised version remains available later as an upgrade if the intercept page
gets built. `PLAYBOOK_LIFECYCLE.md` §L7 has been updated to the shipped copy.

**L7-E2's spec line "Thanks for the trial earlier this year" was corrected** to "Thanks for giving
{{ event.app_name }} a run." This flow triggers on `Cancelled Subscription` — a paid customer — so
thanking them for a trial would be wrong for most recipients.

**Known gap, shared with L2 and L6:** the playbook's "send Tue–Thu, 9–11am recipient timezone" rule
is not implemented anywhere. All delays in all three flows carry `delay_until_weekdays` set to all
seven days. Left consistent rather than making L7 the lone exception; fixing it is a one-setting
change per delay node whenever it is decided to be worth it.

**Still to do before it can go live:** the marketing-consent question below, which gates L7 exactly
as it gates L2 and L6. Turning the flow on is a founder decision and was deliberately left undone.

---

## L2 — built 2026-08-02

`7f83a91` shipped the missing data and it is now deployed (2026-08-02, service restarted onto
`fb501d8`). The flow was then built the same day and is **in Draft**.

**Flow `RWvZ2m` — "PF9 Cart Abandon".** Read back from
`GET /api/flows/RWvZ2m?additional-fields[flow]=definition&include=flow-actions`, not from the canvas:

| Node | Action id | Value |
|---|---|---|
| Trigger | metric `RDTdMQ` | `Started Checkout`, integration `API`. Re-entry allowed. No trigger filter. |
| Delay | `113495607` | 1 hour |
| Email | `113495627` | `L2-E1 - Cart abandon 1h (resume link)`, template `QSsqvH` |
| Delay | `113495854` | 47 hours (1 + 47 = 48h from trigger, per spec) |
| Email | `113495856` | `L2-E2 - Cart abandon 48h (restart link)`, template `Vf7eMc` |

Both emails: sender `PlainSpoken Foundry Nine <support@plainspokenfoundrynine.com>`,
`smart_sending_enabled: false`, and an identical `additional_filters` condition —
metric `XEMaYg` (`Placed Order`, integration `API`), `count equals 0`, timeframe `flow-start`.

**The guard is on each email, not on the trigger.** Klaviyo's trigger-panel filters ("Limit the flow
to trigger only when…") evaluate at flow entry, which is the wrong moment: at t=0 nobody has bought
yet, so an entry-time "hasn't bought" test passes for everyone and never fires again. `additional_filters`
on the send-email action is evaluated immediately before send, which is the moment that matters. Each
email therefore needs its own copy; they are not inherited.

**Smart Sending is deliberately off.** It suppresses anyone emailed in the last 16 hours. A cart-abandon
recovery email dropped because a Trial or Paid onboarding email went out ten hours earlier would
silently lose the highest-intent message in the funnel.

**Link assignment verified at the template level**, since this is the one thing that cannot be checked
by looking at the canvas: `QSsqvH` (E1) contains `{{ event.resume_link }}` and no `resume`-less
variant; `Vf7eMc` (E2) contains `{{ event.restart_link }}` and no occurrence of `resume_link`.

**Still to do before it can go live:** the marketing-consent question below. Turning the flow on is a
founder decision and was deliberately left undone.

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

### Three things that bit while building the flow

All three are recorded below as they were found. The first two are resolved; the third — marketing
consent — is **still open and is what keeps the flow in Draft**.

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

✅ **Handled in the built flow** and verified by reading the two templates back over the API rather
than trusting the canvas: `QSsqvH` (E1) has `resume_link`, `Vf7eMc` (E2) has `restart_link`, and
neither contains the other's.

**⛔ OPEN — this is the one blocker on turning L2 live. The event upserts a profile but does not
grant marketing consent.** That is deliberate — a person
who typed their email into a checkout form has not subscribed to anything, and deciding otherwise is
a consent call, not a code call. Klaviyo will skip flow sends to a non-consented profile unless the
message is configured to allow it, so this has to be settled *before* the flow goes live or L2 will
appear to work and silently deliver nothing.

The 2026-08-03 audit showed this is not specific to L2 or to `_klaviyo_event`: `_klaviyo_sync` does
not grant consent either, so the two live flows are in the same position. See "Consent — audited
2026-08-03".

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

## Draft flows — activation readiness audit, 2026-08-04

L2, L6 and L7 have sat in Draft since 2026-08-02, blocked on consent. Consent is now proven (see
"Consent path proven end-to-end"), so the only thing left is the decision to switch them on. Before
putting that decision up, all three were re-read from the API — **read-only, nothing was changed** —
because switching a flow Live is irreversible per send and there are three deliverable inboxes today.

Read via `GET /api/flows/<id>?additional-fields[flow]=definition`, plus
`GET /api/flows/<id>/flow-actions`, `GET /api/flow-actions/<id>/flow-messages` and
`GET /api/templates/<id>`. Not from the canvas.

> **Revision gotcha.** `additional-fields[flow]=definition` returns HTTP 400
> `"additional-fields must be in []"` on revision `2024-10-15`. It needs `2025-01-15` or later;
> `2025-07-15` was used here. The 400 does not say the revision is the problem, so this reads like a
> malformed request and costs a while to spot.
>
> A second one: `include=flow-actions` returns the actions with `definition` **absent** — names,
> subjects, templates and `additional_filters` all come back as `None`. That looks exactly like an
> unbuilt flow. The populated copy is inside the *flow's* own `definition.actions`, not in `included`.

### As built

| | L2 `RWvZ2m` "PF9 Cart Abandon" | L6 `VgquRn` "PF9 Churn Save" | L7 `RZQKa2` "PF9 Win-back" |
|---|---|---|---|
| Status | draft | draft | draft |
| Trigger metric | `RDTdMQ` Started Checkout | `REutQc` Cancelled Subscription | `REutQc` Cancelled Subscription |
| Trigger filter | none | **none** | `remaining_app_count` numeric equals `0` |
| `profile_filter` | null | null | null |
| Ladder | 1h → E1 → 47h → E2 (48h) | 1d → E1 | 30d → E1 → 14d → E2 (44d) |
| Messages | `UUGHrB`, `SuMhfB` | `SNHiyi` | `WqSzAV`, `R2bqUN` |
| Templates | `QSsqvH`, `Vf7eMc` | `WAn6mF` | `R8kVqk`, `Rr6sCj` |

All five sends agree on the things that matter mechanically: sender
`support@plainspokenfoundrynine.com`, `is_transactional: false`, `use_smart_sending: false`, and an
identical converter exclusion —

```json
{"type": "profile-metric", "metric_id": "XEMaYg", "measurement": "count",
 "measurement_filter": {"type": "numeric", "operator": "equals", "value": 0},
 "timeframe_filter": {"type": "date", "operator": "flow-start"}}
```

`XEMaYg` is `Placed Order`, integration `API`. So nobody who buys (or re-buys) during the delay gets
the next email. On L2 that is the abandon guard; on L6/L7 it is the "they came back" guard.

### Green — checked, correct

- **Merge tags all resolve against real event payloads.** Every tag in every template, listed exhaustively
  rather than spot-checked: `event.app_name`, `event.resume_link` (L2-E1 only), `event.restart_link`
  (L2-E2 only), `event.reactivate_link` (L6-E1, L7-E1), `person.first_name`. `Started Checkout` emits
  `app_name`/`resume_link`/`restart_link`; `Cancelled Subscription` emits `app_name`/`reactivate_link`.
  Nothing references a property that is never sent.
- **The resume/restart trap is avoided.** `QSsqvH` contains `resume_link` and no `restart_link`;
  `Vf7eMc` contains `restart_link` and no `resume_link`. Swapping these is the failure `store_api.py`
  emits both links to make possible, and it would be invisible in the UI.
- **Every tag carries a `|default:`** — `app_name|default:'PF9'`, `first_name|default:'there'` — so a
  missing property degrades to a generic word instead of rendering blank.
- **Unsubscribe present in all five templates.**
- L7's trigger filter is right, and matches what `store_api.py:1338-1341` says `remaining_app_count`
  is for.
- `person.first_name` really is populated, not just defaulted away: `_klaviyo_sync` (`:249-253`) and
  `_klaviyo_event` (`:331-335`) both split the customer name and set `first_name`/`last_name` on the
  profile. It falls back to `there` only when Stripe gave no name at all.

### Amber — found, not fixed

1. **L6 has no trigger filter, and needs the same one L7 has.** `trigger_filter` is `null`, so a
   customer who cancels one app out of five enters the churn-save flow and is asked why they left —
   while still paying for four. `store_api.py` emits `remaining_app_count` on the event *specifically*
   to prevent this, and L7 uses it. L6 was simply not given it. **This is the one substantive build
   defect and it is a customer-visible one.** It is a UI edit (see below).
2. **Template names are useless and that is a live hazard.** Three of the five still carry the clone
   artifact `2026-08-02 <HH:MM> PF9 — Trial Day 3: Check-in` (`QSsqvH`, `Vf7eMc`, `WAn6mF`), one reads
   `2026-08-02 20:34 Untitled email template` (`R8kVqk`), and one has **no name at all** — `null`
   (`Rr6sCj`). The Klaviyo template list is therefore three near-identical rows plus two blanks, none
   describing its contents. Editing the wrong one later is a realistic mistake with no undo. The
   *message* names are fine (`L2-E1 - Cart abandon 1h (resume link)` etc.); it is only the templates.
3. **L2-E1's subject asserts a cause it cannot know.** `Stripe hiccup on your {{ event.app_name }}
   subscription?` with preview `If it was a card issue, here's the link to retry.` The trigger is
   `Started Checkout` with no purchase — which is *usually* hesitation, not a declined card. Telling
   someone who chose not to buy that their payment failed is wrong and slightly alarming. Copy, not
   mechanism; it changes nothing about whether the flow works.
4. **Smart Sending is off on all five, deliberately** (documented under L2 — it would drop the
   highest-intent email in the funnel). Worth re-stating as a live consequence rather than a setting:
   with three flows on and no frequency cap, one person can legitimately receive several PF9 emails
   in a short window. Acceptable at current volume; revisit if the flow count grows.

### What activation cannot be done by

Every flow read in this audit was a `GET`. **No write endpoint was tried**, deliberately — a probe
against a live flow risks being the change it is testing. So the following is the working assumption,
not an observation: Klaviyo exposes flow messages and flow definitions for reading, and the documented
mutation is `PATCH /api/flows/<id>` carrying `status` only, which would switch a flow Live but cannot
add L6's missing trigger filter. On that reading both the L6 fix and the activation are **UI work, and
the UI is the founder's**. If someone later finds a definition-write endpoint, that changes the *how*,
not the decision — activation still sends real mail and still needs a human to choose it.

> **Probed and confirmed at activation time, 2026-08-04** — see the section below. Malformed-body
> probes: `PATCH /api/flows/<id>` → **400** (exists), `PATCH /api/flow-messages/<id>` → **405** (read-only),
> `PATCH /api/flow-actions/<id>` → **404 "No valid revisions found for method"** (does not exist).
> The assumption held, and the gap it leaves turned out to matter — see "the trap that was avoided".
> Note which one is missing: `flow-actions` is precisely where the Draft/Live state of each send is
> stored, so the single writable endpoint is the one that cannot switch an email on.

Two practical notes for whenever it happens:

- **Fix L6's trigger filter before activating L6**, or activate L2 and L7 only. Activating L6 as built
  ships a known defect.
- **The canary needs a fresh checkout.** Flows do not backfill, so the `Started Checkout` event
  already sitting on `xfree143+consenttest@gmail.com` will not pull it into a flow switched on
  afterwards. One `curl` against the checkout endpoint after activation produces a canary that
  actually qualifies.

---

## L2 and L7 activated — 2026-08-04 (live, sending)

**`RWvZ2m` (Cart Abandon) and `RZQKa2` (Win-back) are Live. `VgquRn` (Churn Save) was deliberately
left in Draft** until its missing trigger filter is added. Done in the Klaviyo UI on founder
instruction, after the audit above.

Final state, read back from the API rather than from the canvas. Flows activated at **12:52:16 UTC**
(L2) and **12:54:09 UTC** (L7), per each flow's `updated` attribute:

| Flow | flow status | send action | message | action status |
|---|---|---|---|---|
| L2 `RWvZ2m` | **live** | `113495627` | `UUGHrB` L2-E1 - Cart abandon 1h (resume link) | **live** |
| | | `113495856` | `SuMhfB` L2-E2 - Cart abandon 48h (restart link) | **live** |
| L7 `RZQKa2` | **live** | `113497604` | `WqSzAV` L7-E1 - Win-back 30d | **live** |
| | | `113498550` | `R2bqUN` L7-E2 - Win-back 44d | **live** |
| L6 `VgquRn` | draft | `113496376` | `SNHiyi` L6-E1 - Churn save 24h | draft |

**↑ This table is a snapshot of ~12:55 UTC, kept as written.** L6's row is no longer current: its
trigger filter was added and it was switched on later the same day. See *"L6 switched on — all three
lifecycle flows now live"* below for the current state.

> **Read the status off the action, not the message.** The column above is deliberately titled
> *action* status. A `flow-message` object carries no status at all — its attributes are exactly
> `channel`, `content`, `created`, `name`, `updated`. The Draft/Live control the UI draws on the
> message card is stored on the parent `SEND_EMAIL` **flow-action**. So `GET /api/flow-messages/<id>`
> can never answer "will this send?"; `GET /api/flows/<id>/flow-actions` is the endpoint that can.
> This was nearly recorded the wrong way round here — the first draft of this table called the column
> "message status", which would have sent the next reader to the one endpoint that omits it.

### The trap that was avoided, which is the real finding here

**A Klaviyo flow has two independent status levels: the flow's, and each send action's.** A flow can
read `live` while an individual send action sits at `draft`, in which case profiles enter it, wait out
the delays, reach that step and are silently skipped. Nothing errors. The flow's analytics show
recipients entering.

This is not theoretical — **it is how the day-27 pre-charge notice was switched off.** Flow `X2tesT`
(`PF9 Trial Onboarding`) is `live`; inside it, action `107908224` holding message `ReYNde`
("Trial Day 27 — Pre-Charge Notice") is `draft`, while the other two send actions — `107907408`
(`VpT7Fy`, Day 1) and `107907514` (`YpvAcX`, Day 3) — are `live`. That is the mechanism, and it was
found by reading the reference flow rather than by being told.

The consequence for activation: **the API can set flow status but not send-action status.** Had these
flows been switched on with `PATCH /api/flows/<id>` — the obvious scripted route, and the one the
audit above assumed was available — both would have gone `live` with all four sends still `draft`,
reported success, and sent nothing. That is the identical shape to the `subscription_started` bug
that sat undetected for two months: a green result with no delivery behind it. Worth stating plainly
as the rule: **on a Klaviyo flow, "status: live" is not evidence that anything sends. Check each
send action's own status.**

### Two UI behaviours worth knowing

- **Setting the first message to Live flips the whole flow to Live, silently.** The `Review and turn
  on` button was never clicked; changing L2-E1's dropdown from Draft to Live turned the flow header
  from `Draft` to `Live` on its own, with no confirmation dialog and no summary of what was about to
  start sending. Whatever review that button offers, it is trivially bypassed by the control sitting
  right next to it.
- **The status dropdown opens downward and its `Live` option is clipped** below the viewport when the
  card sits low on the canvas. Clicking an option you cannot see does nothing, and the menu stays open
  looking as though the click registered. Zoom the canvas out until the whole menu fits before
  clicking, and re-read the dropdown afterwards.

### Canary

Flows do not backfill, so a fresh trigger was fired after activation:

```
POST https://app.plainspokenfoundrynine.com/store-api/create-checkout-session
{"product":"FLOWTRACK","email":"xfree143+consenttest@gmail.com", ...}   → HTTP 200
```

Confirmed landed in Klaviyo, read back from `GET /api/events`:

```
2026-08-04T12:55:25+00:00  xfree143+consenttest@gmail.com  app=FLOWTRACK
   resume_link  = https://checkout.stripe.com/c/pay/cs_live_a1wT1ejg4P4CCK7NmMzPjg1Q033F…
   restart_link = https://store.plainspokenfoundrynine.com/?product=FLOWTRACK
```

Both links populated, `app_name` set. L2's first step is a `TIME_DELAY` of `delay_seconds: 3600`
(the second is `169200`, i.e. 47h more, making E2's "48h" the total elapsed since trigger).
**L2-E1 is therefore due at approximately 13:55 UTC** into an inbox we own.

The same profile also has an earlier `Started Checkout` at **12:29:35 UTC** for TASKFLOW, from a
failed endpoint attempt. It predates L2's activation at 12:52:16, so by the no-backfill rule it did
**not** enrol and should produce no mail — which makes it a free negative control. If a TASKFLOW
cart-abandon email turns up around 13:29 UTC, the no-backfill assumption recorded throughout this
document is wrong and much of the timing reasoning here needs revisiting. A dead Stripe Checkout session was created and will expire by itself — no card entered,
no charge. That send is the first end-to-end proof that a PF9 lifecycle email actually reaches an
inbox, and **it has not been observed yet** — do not record this as proven until the mail arrives.

> **Endpoint gotcha, cost a couple of attempts.** The store API is on
> `app.plainspokenfoundrynine.com/store-api`, **not** `store.plainspokenfoundrynine.com`, and the
> Blueprint prefix is `/store-api`, not `/api/store`. Both wrong guesses return nginx's bare
> **405 Not Allowed**, which reads like a method problem rather than a wrong host.

### The three follow-ups — closed 2026-08-04, same day

All three were raised above as open. Two were real and are fixed; the third turned out to rest on a
false premise, which is recorded here rather than quietly dropped.

**1. L6's trigger filter — FIXED.** Added in the UI; the API cannot write flow definitions either.
L6's trigger condition is now byte-identical to L7's, verified by reading both back and comparing:

```json
{"type": "metric-property", "metric_id": "REutQc", "field": "remaining_app_count",
 "filter": {"type": "numeric", "operator": "equals", "value": 0}}
```

Both flows hang off the same metric `REutQc` (Cancelled Subscription); the filter is what separates
"cancelled one app of several" from "actually gone". **L6 was then switched on — see below.**

**2. L2-E1's subject — FIXED.** Now `still thinking about {{ event.app_name|default:'PF9' }}?`,
preview `Your link's still live if you want it.` The `|default:` filter is preserved.

Worth noting what the audit turned up on the way: **the email body was never the problem.** It reads
*"Sometimes that's a card issue, sometimes it's second thoughts"* and then branches to cover both,
which is honest. Only the subject and preview asserted a failure. So the fix was not "rewrite the
email", it was "make the subject agree with the body it is attached to" — and the new subject matches
the body's own second-thoughts branch. Had only the flagged subject been changed without reading the
body, the change would have been right by luck rather than by knowing.

**3. Template names — NOT a real issue; the earlier entry was wrong.** It claimed the risk was
"editing the wrong one now changes a live email". That premise does not hold: **none of the five
flow templates are in the template library.** `GET /api/templates` returns 6 templates, all cleanly
named, and `QSsqvH` / `Vf7eMc` / `R8kVqk` / `Rr6sCj` / `WAn6mF` are not among them. They are
message-embedded, reachable only by opening that specific message inside the flow editor — where the
message name is already correct (`L2-E1 - Cart abandon 1h (resume link)` and so on).

The tell was a write probe: `PATCH /api/templates/Rr6sCj` returns **404 "Template with id 'Rr6sCj'
does not exist"** while `GET` on the same id returns it fine. A GET-visible, PATCH-invisible template
is an embedded one. So the ugly `2026-08-02 19:48 PF9 — Trial Day 3: Check-in` names are clone
artifacts on objects nobody browses, with no live-email risk attached. Renaming them would have been
busywork justified by a hazard that was never there. **Closed as won't-fix.**

### L6 switched on — all three lifecycle flows now live

Once the trigger filter was in, L6 was activated on founder instruction. Set via the **message**
dropdown (Draft → Live), not the `Review and turn on` button; the flow header flipped to Live on its
own again, confirming the silent-flip behaviour recorded above is repeatable and not a one-off.

Full state, every field re-read from the API after the change:

| Flow | flow | send action(s) | action status | trigger filter | converter exclusion |
|---|---|---|---|---|---|
| L2 `RWvZ2m` | live | `113495627`, `113495856` | live, live | none (correct — cart abandon) | present on both |
| L7 `RZQKa2` | live | `113497604`, `113498550` | live, live | `remaining_app_count = 0` | present on both |
| L6 `VgquRn` | live | `113496376` | live | `remaining_app_count = 0` | present |

Two things checked deliberately rather than assumed:

- **The trigger filter survived the status change.** Editing a definition and then flipping status are
  separate writes; the filter was re-read afterwards, not before.
- **All five send actions still carry the converter exclusion** (`profile-metric XEMaYg count = 0
  since flow-start`). That is the guard which stops us emailing someone who already came back, and it
  matters more now that all three flows are live at once.

Note that L6 and L7 share a metric *and* now share a filter, so a fully-churned customer gets the L6
churn-save at day 1 and then L7 at day 30 and day 44. That is the intended ladder, not a duplicate.

**Smart Sending is off on all five** — unchanged, still the open amber from the original audit. With
three live flows on overlapping audiences that is now the most likely source of a customer getting
more mail than intended, so it is the next thing worth a decision.

**↑ Superseded the same day.** That decision was taken within the hour — see *"Smart Sending turned
on"* immediately below. This paragraph is kept as the statement of the problem that prompted it.

### Smart Sending turned on — 2026-08-04, four of five

Enabled on founder instruction, per send action, in each message's **Email details → Settings →
"Skip recently emailed profiles"** — scroll past the template preview, it is below the fold. The
setting is per-message; a guess at an account-level page (`/settings/account/emails`) returned a
Klaviyo 404, which shows only that that URL is wrong, not that no account-level control exists.
**The window is 16 hours**, read off the control's own caption rather than from documentation.

Verified from the flow definition API afterwards, not from the canvas:

| Send action | Message | `smart_sending_enabled` |
|---|---|---|
| `113495627` | L2-E1 - Cart abandon 1h | **false — deliberately, see below** |
| `113495856` | L2-E2 - Cart abandon 48h | true |
| `113497604` | L7-E1 - Win-back 30d | true |
| `113498550` | L7-E2 - Win-back 44d | true |
| `113496376` | L6-E1 - Churn save 24h | true |

**The field is `smart_sending_enabled`, nested in `data.message` of a `send-email` action** — not
`use_smart_sending`, and not on the action itself. A first check looked for the wrong key against the
wrong node type (`SEND_EMAIL` rather than `send-email`), found nothing, and printed a clean-looking
report with no rows in it. An empty result is not a negative result; it printed the flow status
happily, which made it look like it had worked. Anything checking these flags should assert it found
five actions before believing what it says about them.

**Why L2-E1 was left off.** The canary send was in flight into
`xfree143+consenttest@gmail.com`, due ~13:55 UTC from that exact action. Smart Sending is evaluated
at send time, so enabling it first would have risked Klaviyo silently dropping the one email this
whole workstream is trying to observe arriving. **As of this commit it is still off** — that is a
loose end, not a decision: it is to be switched on once the canary is resolved, and this table's
first row must be corrected to `true` when it is. If the row still reads `false` and the Canary
section below is resolved, the follow-through was dropped.

**What this trades away.** Smart Sending **skips, it does not delay**. If the recipient received any
other email inside the 16 hours, the lifecycle email is dropped entirely, not sent late. So this buys
protection against over-mailing overlapping audiences at the price of a *new* silent-non-send path —
the same shape of failure as the day-27 email and the two-month `subscription_started` bug. It is the
right trade with three flows live on overlapping audiences, and it is one checkbox to reverse, but
"the email didn't send" now has two innocent explanations instead of one. Klaviyo is understood to
surface these as *Skipped* in per-message analytics, which would be the place to look before assuming
a flow is broken — **that is from the vendor's description, not observed here**, and no PF9 message
has been skipped yet to confirm it. Worth confirming the first time a send goes missing.

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
- **That Klaviyo actually skips a non-consented profile.** The 2026-08-03 consent finding rests on
  Klaviyo's documented behaviour applied to observed config, not on a send watched failing. No live
  send test was run. A single real send to a `NEVER_SUBSCRIBED` profile would settle it, and should
  be done before any fix is judged to have worked.
- ~~**That `_klaviyo_subscribe` works.**~~ ✅ **Verified 2026-08-04** — executed against production and
  read back `SUBSCRIBED`. See "Consent path proven end-to-end".
- ~~**That the consent tick survives the round trip.**~~ ✅ **Verified 2026-08-04 at the API layer, not
  the browser.** `marketing_consent: true` was posted to the live endpoint and arrived as consent. The
  narrow gap left is the last inch: a human clicking the rendered checkbox. The JS that reads it is
  three lines (`index.html` ~1053-1062) and the live page serves them, but no *ticked* box has been
  observed producing that field.
- ~~**`W7gYXU` behaviour under a real subscribe.**~~ ✅ **Verified 2026-08-04** — one profile added, and
  `double_optin: false` on the resulting consent record confirms the explicit `single_opt_in` at
  creation held. No confirmation email was expected and none was looked for.

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
# NOTE: this is a PRESENCE check and presence is NOT authorisation. It reported
# healthy through both the events:write and subscriptions:write outages. Always
# pair it with the scope probe below.
ssh xfree143.taile2beaa.ts.net \
  'P=$(systemctl show pf9-store-api.service -p MainPID --value); \
   tr \\0 \\n < /proc/$P/environ | grep -c "^KLAVIYO_API_KEY=.\+"'

# does the key still carry subscriptions:write?  403 = missing, 400 = present.
# Malformed body on purpose — creates nothing. Run it server-side so the key
# never lands in a transcript. Do NOT use /api/events/ this way: a valid probe
# there creates a metric, and Klaviyo metrics cannot be deleted.
ssh xfree143.taile2beaa.ts.net \
  'set -a; . /opt/pf9-store/pf9-store-api.env; set +a; \
   curl -s -o /dev/null -w "%{http_code}\n" -X POST \
     https://a.klaviyo.com/api/profile-subscription-bulk-create-jobs/ \
     -H "Authorization: Klaviyo-API-Key $KLAVIYO_API_KEY" \
     -H "revision: 2024-10-15" -H "content-type: application/json" --data "{}"'

# WHICH BUILD IS LIVE — the check the health endpoints cannot make.
# gunicorn does not hot-reload, so /health returns 200 for stale code just as
# happily as for fresh. If the start time predates the file mtime, the restart
# never happened, whatever anyone reports. (Incident: 2026-08-04.)
ssh xfree143.taile2beaa.ts.net \
  'systemctl show pf9-store-api.service -p MainPID -p ActiveEnterTimestamp; \
   stat -c "code mtime: %y" /opt/pf9-store/store_api.py'

# multi-app customer count
ssh xfree143.taile2beaa.ts.net "/opt/pf9-store/venv/bin/python -c \"
import sqlite3
c=sqlite3.connect('file:/opt/bridgr/store_leads.db?mode=ro',uri=True)
print(c.execute('SELECT COUNT(*) FROM (SELECT lower(email) e FROM subscriptions \
WHERE status IN (\\\"active\\\",\\\"trialing\\\") GROUP BY e HAVING COUNT(DISTINCT product)>1)').fetchone()[0])
\""
```
