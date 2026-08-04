# Lifecycle Email Sequences

**Stack:** transactional via the existing `store_api.py` SMTP path; marketing via **Klaviyo** (picked and built 2026-05-30 — the earlier Customer.io / Loops / Resend shortlist is closed). All sequences CAN-SPAM compliant with one-click unsubscribe on marketing sends.

This file is the spec — what each sequence should say and why. For which sequences actually exist in Klaviyo today, see `LIFECYCLE_STATUS.md`. Not all of them do.

**Golden rule:** every email drives to exactly one action. If you can't name the action in five words, don't send it.

**Segmentation triggers.** State as of 2026-08-02 — these are not equivalent pieces of work, and
the ones marked *needs code* cannot be turned on from the Klaviyo UI:

- `subscription_active` — Stripe webhook confirms paid. **Wired.** `_handle_subscription_updated`
  syncs the profile on trialing→active and moves it to the Paid list.
- `subscription_canceled` — cancellation event. **Live since 2026-08-02** (`3a88fe7`, deployed at `fb501d8`).
  `_handle_subscription_cancelled` emits a `Cancelled Subscription` metric, which is what L6 and L7
  trigger on — a profile property alone cannot start a flow. It also now evaluates cancellation
  against what the customer still owns, so cancelling one app of several no longer flags them
  churned account-wide.
- `checkout_started` — Stripe checkout session created. **Live since 2026-08-02** (`7f83a91`, deployed at `fb501d8`).
  `create_checkout_session()` now emits a `Started Checkout` event, and conversion emits
  `Placed Order` so the flow can exclude customers who finished. Abandonment used to be invisible by
  construction; it no longer is. What remains for L2 is the flow itself, which cannot be built until
  the deploy lands and one real event creates the metric in Klaviyo.
- `demo_clicked` — visitor clicks any `/demo` link. **Not wired.** Note the form *submission* is
  captured — `/demo-request` pushes to HubSpot — but that is a different, later event than the
  click, and it reaches HubSpot only, never Klaviyo.
- `last_login` / `last_action` per app — to power activation sequences. **Store half shipped
  2026-08-04; app half not started.** The channel this bullet said did not exist now does:
  `POST /store-api/app-activity` takes a login/action ping from an app, keeps a running
  per-(customer, app) summary, and syncs `last_login_at`, `last_action_at`, `last_active_app`,
  `activated_apps` onto the Klaviyo profile plus an `App Activity` event to trigger on. **No app
  calls it yet**, and it stays inert until `ACTIVITY_SECRET` is set on both sides — so the data is
  still not arriving, and no flow should filter on it until a real ping has landed. Contract,
  client snippets and the two open steps are in `LIFECYCLE_STATUS.md`.

Build state for the sequences themselves lives in `LIFECYCLE_STATUS.md`.

---

## Sequence map

| # | Audience | Trigger | Length | Goal |
|---|---|---|---|---|
| L1 | Video viewer, no subscribe | `video_play` + no `subscription_active` in 24h | 3 emails over 7 days | Drive Subscribe |
| L2 | Cart abandon | `checkout_started` + no `subscription_active` in 1h | 2 emails over 48h | Complete checkout |
| L3 | New subscriber onboarding | `subscription_active` | 4 emails over 14 days | Activate 1st key action |
| L4 | Month-1 success | Day 30 post-subscription | 1 email | Keep them, get testimonial |
| L5 | Month-3 expansion | Day 90 post-subscription | 2 emails over 10 days | Add app or upgrade to bundle |
| L6 | Churn-save (pre-cancel) | Cancel intent clicked, not confirmed | 1 page + 1 email | Save the save-able |
| L7 | Win-back | 30 days post-cancel | 2 emails over 14 days | Return at reduced friction |

All sequences stop immediately on human reply or conversion to next stage.

---

## L1 — Video viewer, no subscribe

**Trigger:** `video_play` event fired on the storefront, no `subscription_active` for the same email within 24 hours. (Email is captured if the visitor came in via a paid ad, content download, or outbound sequence — anonymous viewers don't enter L1.)

### L1-E1 — Day 1, 2 hours after video play

**Subject:** The 2-minute version of what you just watched

> Hey {{first_name}},
>
> Saw you watched the **{{app_name}}** video. Quick context in case it helps:
>
> - Flat **${{price}}/mo**. No per-user charge.
> - Subscribe in 60 seconds. No demo to sit through, no sales call.
> - 14-day money-back, cancel anytime.
>
> If you want to compare against what you're using today or see a second app, the whole catalog is here: https://store.plainspokenfoundrynine.com
>
> Subscribe link: {{subscribe_link}}
>
> — {{founder_first}}

### L1-E2 — Day 3

**Subject:** one thing most {{app_name}} buyers miss in the video

> {{first_name}},
>
> Quick follow-up. The detail buyers usually don't notice in the {{app_name}} video is {{feature}}. It's the part that actually saves the 30 minutes a day most teams are losing.
>
> 45-second clip showing it: {{youtube_clip_url}}
>
> Subscribe when you're ready: {{subscribe_link}}
>
> — {{founder_first}}

### L1-E3 — Day 7

**Subject:** closing the loop on {{app_name}}

> {{first_name}} — last note from me on {{app_name}}.
>
> If the timing's off, ignore this. If you've got a question that's blocking the subscribe, reply here — I read every one.
>
> — {{founder_first}}

**KPIs:** open >50%, click >8%, subscribe conversion >4% of entries.

---

## L2 — Cart abandon

**The two emails must use different links.** Stripe expires a checkout session after ~24 hours, so
`{{resume_link}}` — which preserves the exact cart — is dead by the time E2 sends at 48h. E2 uses
`{{restart_link}}`, the storefront card, which never expires but costs the customer a re-typed name
and email. Both are on the `Started Checkout` event. Swapping them ships an expired-session error to
every E2 recipient.

### L2-E1 — 1 hour after `checkout_started`

**Subject:** Stripe hiccup on your {{app_name}} subscription?

> {{first_name}} — saw you started checkout for **{{app_name}}** but didn't finish. Sometimes that's a card issue, sometimes it's second thoughts.
>
> If it's the card, here's the link to retry: {{resume_link}}
>
> If it's the second thoughts, reply and tell me what's in the way — I'll answer honestly, no pressure.
>
> — {{founder_first}}

### L2-E2 — 48 hours after `checkout_started`

**Subject:** {{app_name}} — should I close this out?

> {{first_name}}, if you'd rather not subscribe right now that's completely fine — just let me know and I'll stop reminders.
>
> Link's still live if you change your mind: {{restart_link}}
>
> — {{founder_first}}

**KPIs:** recovery rate >15% of abandoned carts.

---

## L3 — New subscriber onboarding

> ⚠️ **`X2tesT` carries a flow-level profile filter — do not remove it.** Added 2026-08-02:
> `subscription_status not-equals 'cancelled'` **OR** `subscription_status is not set`.
>
> It exists because removal from the trial list prevents *entry* only. By day 27 a cancelled
> profile is already inside a 24-day delay, so without this filter it still receives "your card is
> charged on [date]" — which reads as a billing error to someone who has already cancelled.
>
> The `is not set` half is not redundant: a Klaviyo custom property does not exist until something
> writes it, and a bare `not-equals` risks excluding every profile that lacks the property
> entirely. Keep both halves in **one** condition group (that is Klaviyo's OR). Detail and evidence
> in `LIFECYCLE_STATUS.md`, "Day-27 filter — 2026-08-02".

### L3-E1 — Immediately on `subscription_active`

**Subject:** Welcome — your {{app_name}} login is ready

> {{first_name}},
>
> You're in. Login: {{app_url}}
> Username: {{email}}
> Password: we just sent a set-password link in a separate email.
>
> **Do these three things first** — they take 10 minutes total and get the app delivering value immediately:
>
> 1. {{action_1}} (2 min)
> 2. {{action_2}} (3 min)
> 3. {{action_3}} (5 min)
>
> Stuck? Reply here. Real human.
>
> — {{founder_first}}

Per-app action set (Cowork to maintain):
- **SHIFTLOG:** create first shift template → invite supervisors → log first handoff
- **FLOWTRACK:** import items CSV → set one reorder point → scan first barcode
- **QUALIFI:** create first inspection form → run one inspection → log one NCR
- **REPORTR:** connect one data source → build one dashboard → share link
- **INSPECTR:** create first checklist → run first inspection → review photo log

### L3-E2 — Day 3 (only if key action not yet taken)

**Subject:** 5 minutes to get {{app_name}} working for you

> {{first_name}} — noticed you haven't {{key_action}} yet. That's the step where {{app_name}} starts saving you time.
>
> Here's a 90-second loom walkthrough: {{loom_link}}
>
> Want me to do it with you on a 15-minute screenshare? Reply with a time.
>
> — {{founder_first}}

### L3-E3 — Day 7

**Subject:** what's actually working so far?

> {{first_name}}, one week in. Two questions:
>
> 1. What's working?
> 2. What's broken or confusing?
>
> Reply with a one-liner on each — I'll fix what I can this week.
>
> — {{founder_first}}

### L3-E4 — Day 14

**Subject:** the other apps most {{app_name}} users add next

> {{first_name}},
>
> Two weeks in. Most shops running {{app_name}} add **{{adjacent_app}}** ($${{price}}/mo) around this point — {{reason}}.
>
> Live demo: {{demo_link}}
> Add it from your dashboard: {{upgrade_link}}
>
> Or bundle all 5 apps for $249/mo instead of $335: {{bundle_link}}
>
> — {{founder_first}}

**KPIs:** 80% hit one key action by day 7; 50% hit all three by day 14; 10% add a second app within 30 days.

---

## L4 — Month-1 success & testimonial ask

### L4-E1 — Day 30

**Subject:** 30 days of {{app_name}} — quick ask

> {{first_name}},
>
> One month in. If {{app_name}} has been useful, two small asks:
>
> **(a)** Would you be open to a 2-sentence quote we can use on the site? Whatever you'd honestly say.
>
> **(b)** If you know another shop like yours, a quick forward would mean a lot.
>
> If it's *not* been useful, I want to know that more. Reply with what's not landing.
>
> — {{founder_first}}

**KPIs:** 15% respond with a usable quote (feeds T4 in `PLAYBOOK_CRO.md`).

---

## L5 — Month-3 expansion

### L5-E1 — Day 90

**Subject:** you're paying {{current_spend}} — bundle is $249

> {{first_name}},
>
> You've been on {{app_list}} for 3 months, at ${{current_spend}}/mo.
>
> The 5-app bundle is $249/mo — and the apps you don't have today are {{missing_apps}}.
>
> If one of those is on your list for Q{{next_quarter}}, the bundle math works. Upgrade in two clicks: {{bundle_link}}
>
> If not, ignore — the current plan stays exactly as it is.
>
> — {{founder_first}}

### L5-E2 — Day 100 (only if no upgrade)

**Subject:** {{missing_app}} free for 30 days — see if it fits

> {{first_name}} — one specific offer.
>
> Add **{{missing_app}}** to your account free for 30 days. No card change. If it's not pulling weight, remove it with one click and you never get billed.
>
> Add it: {{trial_link}}
>
> — {{founder_first}}

**KPIs:** 8% of month-3 subscribers take expansion (either add-app or bundle upgrade).

---

## L6 — Churn-save

### L6-Page — Intercept on cancel click

Before the Stripe cancel flow completes, show:

> ### Before you cancel — one question
>
> What's the main reason?
>
> - [ ] Price
> - [ ] Missing a feature
> - [ ] Too hard to use
> - [ ] Business closed / not needed anymore
> - [ ] Something else
>
> *(conditional response based on selection — e.g., "Feature" routes to founder for a same-day email; "Price" offers a 50% month-4 credit to stay; "Business closed" proceeds straight to cancel without friction)*

### L6-E1 — 24 hours post-cancel

**Subject:** closed your {{app_name}} — honest question

> {{first_name}},
>
> Saw you canceled. One question, and a no-hard-feelings policy on the answer:
>
> What *would* have made it worth keeping?
>
> I read every reply and log it against the roadmap.
>
> — {{founder_first}}

**KPIs:** 25% of cancel-clicks saved by the page intercept; 20% reply rate on the follow-up.

---

## L7 — Win-back (30 / 44 days post-cancel)

**Built 2026-08-02 as Klaviyo flow `RZQKa2` "PF9 Win-back", in Draft.** See `LIFECYCLE_STATUS.md`
§"L7 — built 2026-08-02" for the node-by-node record.

The `remaining_app_count = 0` requirement is a **trigger filter** on the flow — correct because it
is an event property, frozen at cancellation time. The "no reactivation" guard is separate: a
send-time `Placed Order = 0 since starting this flow` filter on each email, because that condition
can change after entry.

### L7-E1 — Day 30

The original spec copy for this email merged `{{reason}}` (from the L6 intercept page, which does
not exist) and `{{change}}` (no source at all), so it would have rendered "you mentioned ." to every
recipient. It was **rewritten generically** around the properties `Cancelled Subscription` actually
carries. Shipped copy:

**Subject:** your {{app_name}} data is still there

> {{first_name}},
>
> It's been a month since you closed {{app_name}}. No pitch — just so you know nothing was deleted.
>
> If you want it back, it's one click: {{reactivate_link}}. Everything picks up where you left it.
>
> — {{founder_first}}

If the L6 intercept page is ever built, the personalised "you mentioned {{reason}}" version becomes
available as an upgrade to this email.

### L7-E2 — Day 44 (only if no reactivation)

**Subject:** last one — unsubscribe or keep in touch?

> {{first_name}}, I won't keep pinging. Two options:
>
> - Unsubscribe (no hard feelings): {{unsub_link}}
> - Stay on a quarterly note when we ship something big: no action needed
>
> Thanks for giving {{app_name}} a run.
>
> — {{founder_first}}

(The spec previously read "Thanks for the trial earlier this year." This flow triggers on
`Cancelled Subscription` — a paying customer — so that line was wrong for most recipients.)

**KPIs:** 5% win-back rate.

---

## Writing rules (apply to every email above)

- **From name:** founder's name, not "PF9 Team"
- **Length:** under 100 words, always
- **One CTA:** one link that matters, plus reply-to-founder as the fallback
- **No images, no logos, no fancy layouts** — plain text gets replies, HTML gets deleted
- **Send times:** Tue–Thu, 9–11am in the recipient's timezone
- **Reply-to:** founder's actual inbox for sequences marked "— {{founder_first}}"
- **Unsubscribe:** present on every marketing email; omit from transactional (welcome, cart-abandon, cancel)

---

## Reporting

Add to the weekly report (per `SALES_PLAN.md` §7):
- Per-sequence: sends, open, click, conversion-to-next-stage
- Onboarding activation %: hit all 3 key actions by day 14
- Expansion %: month-3 subscribers taking an upgrade offer
- Churn-save %: cancel-clicks retained by L6

Kill or rewrite any email with open <30% or click <3% after 500 sends. Never let a dead email keep shipping.
