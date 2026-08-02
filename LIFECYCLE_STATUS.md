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
wait 30d → email (day 30) → wait 60d → email (day 90)
```

The day-90 email is **L5-E1, the month-3 expansion pitch, and it is live and sending today.**

---

## Sequence map — spec vs. built

| # | Spec | Built? | Detail |
|---|---|---|---|
| L1 | Video viewer, no subscribe | **No flow** | Needs a `video_play` event. Nothing in `store_api.py` emits one; no flow exists to consume it. |
| L2 | Cart abandon | **No flow** | Needs `checkout_started`. `create_checkout_session()` does NOT sync Klaviyo — the profile is first touched at `checkout.session.completed`, i.e. only *after* success. The abandon case is invisible by construction. |
| L3 | New subscriber onboarding | **Partial** | Trial flow (3 emails @ 0/3/27) + Paid flow both live. Spec says 4 emails over 14 days; actual trial cadence is 0/3/27. Cadence differs from spec — spec not updated, or flow not finished. Not resolved. |
| L4 | Month-1 success | **Live** | Day-30 email in the Paid flow. Whether its content matches the spec's testimonial ask was NOT checked. |
| L5 | Month-3 expansion | **Live but unconditional** | Day-90 email in the Paid flow. See below. |
| L6 | Churn-save | **No flow** | Cancel does sync Klaviyo (`subscription_status: cancelled`, removed from trial list) so the *data* is there; no flow and no intercept page consume it. |
| L7 | Win-back | **No flow** | Same — cancellation data exists, nothing acts on it. |

---

## L5 — the actual open gap

The day-90 expansion email is live. **It has no conditional split.** Both flows contain only
`send-email` and `time-delay` actions — no profile filter, no branch. So every paid subscriber
reaching day 90 gets pitched an app, including one who already owns it.

`b4d80e0` shipped the data to fix that:

| Property | Set where | Purpose |
|---|---|---|
| `app_count` | checkout completed; trialing→active | Integer the split should read. `> 1` ⇒ skip the pitch. |
| `apps_owned` | same | Comma-separated names. Exists so a human opening the profile can audit *why* `app_count` is what it is. |
| `related_app_name` / `_detail` / `_url` | same | The cross-sell target the email renders. |
| `app_name`, `app_price`, `trial_end_date`, `manage_subscription_url` | checkout; trial_will_end | Trial flow merge tags. |
| `subscription_status` | cancelled; trialing→active | `cancelled` / `active`. |

Both are recomputed from the `subscriptions` table on every write, never incremented — Stripe
redelivers webhooks, and a counter would drift upward on replay.

**The split itself does not exist in Klaviyo. `app_count` currently has no consumer.**

### Why it hasn't been built

Production, read 2026-08-02:

```
subscriptions rows : 3
by status          : {active: 2, cancelled: 1}
distinct emails    : 3
customers with >1 app : 0
```

The split would today change the behaviour of **zero** sends. That is the argument for waiting.
The argument against waiting is that the email is already going out unconditionally, so the gap
is live rather than theoretical — the moment a second app is sold, it misfires. It is a
~5-minute change in the Klaviyo UI (add a conditional split before the day-90 send, branch on
`app_count > 1`).

Also note: **existing profiles do not backfill.** `app_count` only lands on a profile when that
customer next hits checkout or converts trialing→active. The 3 current profiles will not have it
until then, so the split must treat "property missing" as `0` — which is the safe direction
anyway, since 0 sends the email, i.e. today's behaviour.

---

## Not verified

Listed so they are not mistaken for "checked and fine":

- **Email bodies.** No flow message content was read. Whether the live emails match the copy in
  `PLAYBOOK_LIFECYCLE.md`, or use the merge tags listed above at all, is unknown.
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
# flows, their status, and step order
#   Klaviyo MCP: get_flows include=flow-actions
#     fields_flow_action=definition.type,definition.id,definition.links.next,
#                        definition.data.value,definition.data.unit
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
