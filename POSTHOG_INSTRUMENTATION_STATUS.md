# PostHog Instrumentation — Status & Next Steps

Done autonomously on 2026-05-31. The **storefront plus the whole app fleet** are now instrumented (see the Fleet Rollout table below). PostHog had **zero events** before this; these changes start the flow.

> ⚠️ **Re-checked 2026-08-04 — this file had been wrong for about two months.**
>
> - *"Nothing was pushed to GitHub or deployed — that's yours to trigger."* **No longer true for the
>   storefront.** All 34 pages carry the snippet, it is committed (`4426d4b`), and `curl` of the live
>   `store.plainspokenfoundrynine.com` returns it. Verified by fetching the live page, not by reading
>   this file.
> - **The fleet half was not re-checked.** 18 apps is a bigger job than this correction, so treat
>   every ✅ in the table below as "written in May", not as "deployed and confirmed". Check per app
>   before relying on it.
> - **`subscription_started` never once fired**, and §1 below told you to fix it the wrong way.
>   Corrected 2026-08-04 — see the strikethrough there.
>
> The lesson worth keeping: a status file ages into a liability. All three claims were cheap to test
> against the live system, and none of them had been.

## Fleet rollout (all apps)

Every app needs `npm install` (Node apps) or `pip install -r requirements.txt` with **python3.12** (Flask apps) before the new code runs. "Client" = pageviews + autocapture (clicks/form submits) + identify. "Server events" = explicit `app_signup` / `app_login` / `core_action_performed`.

| App | Stack | Client | Server events | Activation action |
|---|---|---|---|---|
| Storefront | static HTML | ✅ 34 pages | n/a (GA4 mirror + `subscription_started`) | — |
| FLOWTRACK | Next.js | ✅ | ✅ | scan item |
| SHIFTLOG | Next.js | ✅ | ✅ | submit handoff |
| MAINTAINR | Next.js | ✅ | ✅ | create work order |
| REPORTR | Next.js | ✅ | ✅ | create dashboard |
| INSPECTR | Vite + Express | ✅ | ✅ | submit inspection |
| QUALIFI | Vite + Flask | ✅ | ✅ signup/login (activation via autocapture) | complete inspection |
| LANDLORDR | Flask | ✅ | ✅ (Flask reference) | add property |
| TENANTLINKR | Flask | ✅ (2 templates) | ✅ | maintenance request submitted |
| SUPPORTR | Flask | ✅ | ✅ | ticket resolved |
| EXTRACTR | Flask | ✅ | ✅ | extraction started |
| PERMITR | Flask | ✅ | ✅ | permit created |
| TASKFLOW | Flask | ✅ | ✅ | task created |
| COMPLI | Flask | ✅ | ✅ | policy created |
| BRIDGR | Flask | ✅ (3 templates) | ⬜ via autocapture | — |
| PAPERCLIPR | Flask | ✅ | ⬜ via autocapture | — |
| WEALTHWATCH | Flask | ✅ | ⬜ via autocapture | — |
| BABYSTOCK | Flask | ✅ (18 pages) | ⬜ via autocapture | — |
| OPSIQ | Flask (API only, coming soon) | ⬜ skipped | ⬜ | add at launch |

The ⬜ Flask apps still produce a working funnel: autocapture records their login/register form submits and core-action button clicks, which you turn into funnel steps in PostHog. To upgrade any of them to clean named server events, copy the LANDLORDR pattern (`app/analytics.py` + 3 call sites). MARKUPR / PF9DOCS (Next, no auth yet) and VAULTCRM were left out — no live auth surface.

---

> One thing to confirm first: the PostHog **region**. I used `https://us.i.posthog.com`. If your project is on EU, change every `api_host` / `NEXT_PUBLIC_POSTHOG_HOST` to `https://eu.i.posthog.com`. Check in PostHog → Settings → Project; events silently won't arrive if the region is wrong.

---

## 1. Storefront (`pf9-store/`) — DONE, no build step needed for the snippet

- Added the PostHog loader to **all 34 HTML pages** (`posthog.init` with your project key).
- Added a **mirror shim**: every existing `gtag('event', name, params)` now also fires `posthog.capture(name, params)`. So these already flow to PostHog with no further work: `checkout_started`, `subscribe_modal_open`, `waitlist_open`, `waitlist_submit`, `video_play`, `support_email_click`, `lead_magnet_capture`.
- ~~Added `subscription_started` on checkout return in `index.html` — **requires one change you must make**: set the Stripe `success_url` … to include `?checkout=success&product=<app>&email=<email>`.~~
  **Wrong, and fixed 2026-08-04.** The listener was on `index.html` watching `?checkout=success`,
  while `success_url` has always pointed at `login.html?subscribed=<app>&session_id=…` — wrong page
  and wrong parameter, so the event could not fire and never did, for two months. It now fires from
  `login.html` off the parameter that was already there: **no billing-code change, no `store_api.py`
  redeploy.** Do not apply the old instruction — besides being unnecessary, `&email=` would put a
  customer's address into a URL, and so into logs, referrers and history. Full reasoning in
  `POSTHOG_RUNBOOK.md` §3. **Still unobserved:** no checkout has completed since, so this is fixed in
  code and not yet watched firing.
- GA4 is untouched and still runs in parallel. Don't remove gtag until PostHog is trusted.

**Verify:** open the live store, then PostHog → Activity. You should see `$pageview` immediately and `checkout_started` when you open a subscribe modal. (Static files — just deploy as usual; no rebuild required since the snippet is inline HTML.)

---

## 2. FLOWTRACK (`FLOWTRACK/`) — DONE in code, needs `npm install`

New files: `src/lib/posthog.ts` (server helper), `src/components/posthog-provider.tsx` (client).
Edited: `src/app/layout.tsx` (provider wrap), `src/app/api/auth/register/route.ts` (`app_signup` + identify), `src/lib/auth.ts` (`app_login` via NextAuth events), `src/app/api/scan/route.ts` (`core_action_performed`, action=scan → activation), `package.json` (+posthog-js, +posthog-node), `.env` (keys, gitignored).

**To make it live on your Mac:**
```bash
cd FLOWTRACK
npm install            # pulls posthog-js + posthog-node
npm run build          # or npm run dev — confirm it compiles
```
**Verify:** register a test user → `app_signup` in PostHog; log in → `app_login`; scan any item → `core_action_performed`. All carry `app: "flowtrack"`.

Note: activation is **derived in PostHog** as the *first* `core_action_performed`, rather than a separate coded event — less code on the hot scan path, same funnel result.

---

## 3. The funnel (build once events arrive)

In PostHog → Funnels, breakdown by `app`:
`$pageview` → `checkout_started` → `subscription_started` → `app_signup` → `core_action_performed` (first = activation).

⚠️ **The identity claim here was wrong and the fix changed it further.** This used to say identity
stitches storefront→app by email, with the storefront identifying "on the Stripe success param".
That `posthog.identify` sat in the same unreachable block as the broken `subscription_started`, so it
never ran — and it was removed on 2026-08-04 rather than repaired, because it depended on `&email=`
in the URL. What actually holds now:

- **Within the storefront**, the funnel joins on the browser's anonymous `distinct_id`. That covers
  `$pageview` → `checkout_started` → `subscription_started` and needs no email at all.
- **Across the storefront→app boundary**, there is *no* identity stitch from the storefront side —
  it has no email to offer and is not going to put one in a URL. The app side reportedly calls
  `identify(email)` at signup, but that is this file's May claim and **was not re-checked**; either
  way one-sided identification does not join anything. Assume the last two steps do not join.

That is a real gap, recorded rather than papered over. The right fix is a server-side
`subscription_started` from the Stripe webhook — which already knows the email, and can send it in a
request body instead of a URL. It is not built.

---

## 4. Replicating to the other apps

The repos split two ways (per CLAUDE.md). Pattern differs:

**Next.js apps** — INSPECTR, MAINTAINR, MARKUPR, PF9DOCS, QUALIFI, REPORTR, SHIFTLOG. Copy the FLOWTRACK pattern verbatim:
1. Copy `src/lib/posthog.ts` and `src/components/posthog-provider.tsx` (change `APP_SLUG`).
2. Wrap `app/layout.tsx` body in `<PostHogProvider>`.
3. Add `captureServer("app_signup", email, …)` + `identifyServer` in the register route.
4. Add the `events.signIn` → `app_login` block in the NextAuth config.
5. Pick the app's activation action (see plan §5) and emit `core_action_performed` there.
6. Add the two deps + 3 env lines; `npm install`.

**Flask apps** — BABYSTOCK, BRIDGR, COMPLI, EXTRACTR, LANDLORDR, OPSIQ, PAPERCLIPR, PERMITR, SUPPORTR, TASKFLOW, TENANTLINKR, WEALTHWATCH. Different stack:
1. `pip install posthog` (use `python3.12`, per CLAUDE.md).
2. Add the JS snippet to the base Jinja template `<head>` (same loader as the storefront) for pageviews/autocapture.
3. Server-side: `from posthog import Posthog; ph = Posthog(project_api_key, host=…)`; call `ph.capture(distinct_id=email, event="app_signup"/"app_login"/"core_action_performed", properties={"app": "<slug>"})` in the register, login, and core-action views.
4. Add keys to that app's `.env`.

I can do any of these on request — say which app and I'll instrument it the same way. Reasonable order: the live paid apps first (QUALIFI, SHIFTLOG, REPORTR, INSPECTR, MAINTAINR on the Next side; LANDLORDR, TENANTLINK, EXTRACTR, PERMITR, TASKFLOW on the Flask side).

---

## 5. What I did NOT touch

- No `git commit` / `git push` (your call; `.env` stays gitignored either way).
- No deploy.
- GA4 left running in parallel.
- No `npm install` run against the mounted folder (would risk your Mac's native modules).
