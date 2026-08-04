# PF9 PostHog Tracking Plan

Goal: one consistent event taxonomy across the **storefront** and all **15 apps**, so the full journey — visitor → demo → checkout → signup → activation → retention → churn — lives in a single funnel, broken down by app.

PostHog project: `Default project` (id 448440). Status as of writing: **no events ingested yet** — the SDK isn't installed anywhere. GA4 is live on the storefront only.

---

## 1. Design principles

- **Event names are snake_case, past-tense, product-agnostic.** The same event (`app_activated`) fires from every app; the `app` property tells them apart. This is what lets you compare conversion across all 15 products on one chart.
- **Every event carries an `app` property** — `"storefront"`, `"flowtrack"`, `"qualifi"`, etc. Never bake the product name into the event name.
- **Identify by email.** The storefront is anonymous until checkout; apps know the user at signup. Calling `identify(email)` in both places stitches the pre-purchase and post-purchase journey into one person.
- **Use PostHog group analytics** for two group types: `account` (the paying customer / company) and `app` (the product). This gives you per-account retention and per-app funnels without custom SQL.
- **Server-side for money + identity, client-side for behavior.** Signup, subscription, and cancel events fire from the server (trustworthy). Page views, clicks, and feature usage fire from the browser.

---

## 2. Identity & groups

| Concept | PostHog mechanism | Where set |
|---|---|---|
| Visitor | anonymous `distinct_id` (auto) | storefront snippet |
| Known user | `identify(email)` | Stripe success page + app signup |
| Person properties | `$set`: `email`, `signup_app`, `plan`, `created_at` | on identify |
| Account/company | `group("account", <account_id>)` | app layout + Stripe webhook |
| Product | `group("app", <app_slug>)` | every capture (via default property) |

Stitching rule: use the **email** as the distinct_id at Stripe checkout and again at app signup. PostHog merges the anonymous storefront session into that person automatically.

---

## 3. Storefront events (`pf9-store`, static HTML)

The storefront already fires these to GA4. Mirror each one to PostHog with `posthog.capture(...)`, and add the two missing money events. Snippet goes in the shared `<head>` next to the existing GA4 block (every page, or inject via the build).

| Event | Fires when | Key properties | Status today |
|---|---|---|---|
| `$pageview` | every page load | auto (`$current_url`, referrer, utm) | auto |
| `product_demo_played` | demo video click | `app` | exists as `video_play` |
| `subscribe_modal_opened` | Subscribe clicked | `app`, `price` | exists as `subscribe_modal_open` |
| `checkout_started` | redirect to Stripe | `app`, `price` | exists |
| `waitlist_opened` | waitlist modal open | `app` | exists as `waitlist_open` |
| `waitlist_submitted` | waitlist form submit | `app`, `email` | exists as `waitlist_submit` |
| `support_email_clicked` | support mailto click | `subject` | exists |
| `subscription_started` | `login.html`, the Stripe success landing page | `app`, `amount`, `source` | ✅ shipped 2026-08-04 — **no `email`**, see note |
| `lead_magnet_downloaded` | lead-magnet form submit | `asset` | **add** (you have a `/lead-magnets/` dir) |

Note: keep GA4 as-is for now — run both in parallel. Don't rip out gtag until PostHog is trusted.

**Why `subscription_started` dropped `email`, and gained a `source`.** The row above specified
`email` as a property. It is deliberately not sent. Carrying it would mean putting the customer's
address in `success_url`, i.e. in the query string — from where it leaks into server logs, `Referer`
headers and browser history. The funnel does not need it: PostHog links this event to the earlier
`checkout_started` through the browser's own `distinct_id`, which is the same join without the PII.
`plan` was dropped too, for a duller reason — nothing in the storefront has a plan concept, so it
would have been a permanently-null column. `source` was added because it is genuinely useful once
apps start emitting their own conversion events. **Shipped but not yet observed:** no checkout has
completed since, so this is code-correct and unwatched.

---

## 4. App events (Next.js apps — FLOWTRACK is the template)

Install `posthog-js` (browser) + `posthog-node` (server). Instrumentation points are identical across apps because they share the route-group structure (`(auth)`, `(dashboard)`).

| Event | Fires from | File (FLOWTRACK example) | Properties |
|---|---|---|---|
| `$pageview` / `$pageleave` | PostHogProvider | `src/app/layout.tsx` | auto |
| `app_signup` | register success (server) | `src/app/api/auth/register/route.ts` | `app`, `email`, `plan` → then `identify` |
| `app_login` | NextAuth signIn callback | `src/app/api/auth/[...nextauth]/route.ts` | `app`, `email` |
| `app_activated` | first real action (see §5) | per-app dashboard handler | `app`, `activation_type` |
| `core_action_performed` | the app's main repeated verb | per-app | `app`, `action` |
| `subscription_started` | Stripe webhook (server) | shared webhook handler | `app`, `account_id`, `plan`, `amount` |
| `subscription_canceled` | Stripe webhook (server) | shared webhook handler | `app`, `account_id`, `reason` |

`app_activated` fires **once per user** — gate it so it only sends the first time the activation action happens.

---

## 5. "Activation" defined per app

Activation = the moment a trial user gets first value. This is the most important event to get right; it's what separates tire-kickers from real adopters. Proposed definitions (adjust to taste):

| App | Activation = first time they… |
|---|---|
| FLOWTRACK | scan/receive a stock item |
| QUALIFI | complete an inspection / open an NCR |
| SHIFTLOG | submit a shift handoff |
| REPORTR | build or view a dashboard |
| INSPECTR | submit a field inspection |
| LANDLORDR | add a property + tenant |
| TENANTLINK | tenant submits first request |
| PERMITR | issue a permit |
| TASKFLOW | create a board with a task |
| MAINTAINR | create a work order |
| EXTRACTR | run first extraction |
| SUPPORTR | resolve first ticket |
| COMPLI (free) | upload first policy / complete a checklist |
| MARKUPR / OPSIQ | (coming soon — define at launch) |

---

## 6. The funnel you asked for

Once the above is live, this is a single PostHog funnel, breakdown by `app`:

```
$pageview (storefront)
   → product_demo_played
   → checkout_started
   → subscription_started
   → app_signup
   → app_activated
   → retained (returns within 7 / 30 days)
```

What it answers immediately:
- Which of the 15 apps convert demo → paid best, and which leak.
- Where the drop is: demo interest vs. checkout intent vs. actual activation.
- Trial-to-value time per app (signup → activated).
- Retention by app and by account (via group analytics).

---

## 7. Rollout order

1. **Storefront** — add PostHog snippet + mirror existing events + add `subscription_started` on the Stripe success page. (Half a day; instant top-of-funnel visibility.)
2. **One app end-to-end** — FLOWTRACK as the reference: provider, signup, login, activation, Stripe webhook events. Prove the full funnel on one product.
3. **Replicate** — the other live apps share FLOWTRACK's structure, so it's copy-adapt-set-activation-event each.
4. **Verify** — confirm events land, identities stitch storefront→app, then build the funnel + a retention chart and turn off the GA4 dependency if you want.

---

## 8. Secrets / config

- Project API key (safe for browser, `phc_` public ingest key): `phc_kqFGBkXKCodfJGJBFdZs3h9Qm43AQaqnyCiETDAwzgmw`
- Put it in each app's existing `.env` as `NEXT_PUBLIC_POSTHOG_KEY` and `NEXT_PUBLIC_POSTHOG_HOST`. (Your apps already use `.env`; it's gitignored per CLAUDE.md — keep it that way.)
- Server events (`posthog-node`) can reuse the same project key for ingest.
