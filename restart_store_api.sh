#!/usr/bin/env bash
#
# Restart-only deploy for pf9-store-api.service.
#
# /opt/pf9-store is synced from the repo by /opt/pf9-store-pull.sh — a root cron
# job that runs EVERY MINUTE. Identified 2026-08-04; this comment previously said
# only "something root-side", which was true but useless. It is not a GitHub
# Actions runner: the only workflows in this repo are Pages and CodeQL. In full:
#
#     git fetch origin main
#     if HEAD != origin/main: git pull --quiet && systemctl reload nginx
#
# Note what that last command reloads. NGINX — never pf9-store-api. That single
# detail is the reason this script exists. Static files under /opt/pf9-store go
# live by themselves within 60s of a push; Python never does, because nothing in
# the automated path signals gunicorn. So a push looks like a deploy, the site
# visibly updates, and the API keeps serving whatever it imported hours ago.
#
# Confirm the tree is current before restarting — `git -C /opt/pf9-store diff
# HEAD origin/main` should be empty. Within a minute of a push it already will be.
#
# The restart is needed because gunicorn does not hot-reload: the workers keep
# serving whatever code they imported at start. A healthy /health therefore
# proves nothing about which version is live. The decisive check is that the
# new MainPID's start time is later than store_api.py's mtime.
#
# Guards below catch a bad file or a missing secret before the service goes
# down rather than after. EXPECT_MD5 must be bumped by hand whenever
# store_api.py changes, or every restart aborts on the checksum.
#
# Needs a real sudo password — pf9-store-api is missing from the NOPASSWD list
# that ~12 sibling PF9 services are on, so this cannot be run as a one-shot
# `ssh ... sudo ...`. Log in first, then run it:
#   ssh -t xfree143.taile2beaa.ts.net
#   sudo bash /opt/pf9-store/restart_store_api.sh
#
# If you are ALREADY on xfree143, skip the ssh line. The host holds no
# authorized_key for itself, so that command fails with "Permission denied
# (publickey)". On 2026-08-04 that failure scrolled past unnoticed, the sudo
# prompt underneath it went unanswered, and the restart was reported as done
# while the 10h-old process kept serving — every health check green throughout.
# Trust the MainPID change and the mtime comparison below, never the impression
# that the command ran. `grep sudo /var/log/auth.log | tail` settles it: this
# script's invocations are logged there by name.
#
set -euo pipefail

STORE_DIR=/opt/pf9-store
STORE_API=$STORE_DIR/store_api.py
VENV=$STORE_DIR/venv
UNIT=pf9-store-api.service
PORT=5011
EXPECT_MD5=e11c3c6d5bea0a1a41e9f90373587a6d   # /demo-request emits Lead Captured
# previous: a0892470ad7473c7e5511f8f8010468e   (Stripe cancel reason -> Cancelled Subscription event)
# before:   6628991de9ce300ba05dfa038c6b0b17   (day-27 pre-charge notice sends from the webhook)
# before:   4e2d690e869dc97e0d03cff6202a220e   (checkout consent tick -> _klaviyo_subscribe)
# before:   01e45e4187644ae68e9ce68d176310cd   (trial start writes subscription_status=trialing)
BRIDGR_ENV=/opt/bridgr/.env
OVERRIDE_ENV=$STORE_DIR/pf9-store-api.env

say(){ echo -e "\n=== $* ==="; }
[ "$(id -u)" -eq 0 ] || { echo "must run as root (use sudo)"; exit 1; }

say "Preflight: on-disk code matches the committed build"
GOT_MD5=$(md5sum "$STORE_API" | awk '{print $1}')
echo "  md5=$GOT_MD5 (expected $EXPECT_MD5)"
[ "$GOT_MD5" = "$EXPECT_MD5" ] || {
  echo "  !! mismatch — the runner may not have synced yet. Aborting."; exit 1; }

say "Preflight: code compiles under the service venv"
"$VENV/bin/python" -m py_compile "$STORE_API" && echo "  OK"

say "Preflight: STRIPE_WEBHOOK_SECRET present (webhook is fail-closed without it)"
if grep -qE '^STRIPE_WEBHOOK_SECRET=.+' "$BRIDGR_ENV"; then
  echo "  present in $BRIDGR_ENV"
else
  echo "  !! missing — /store-api/stripe-webhook would 500 on every event. Aborting."; exit 1
fi

say "Check: KLAVIYO_API_KEY (lifecycle emails are a no-op without it)"
# Presence is NOT authorisation, and this check used to conflate them. On
# 2026-08-02 the key was present here and reported "ACTIVE" while every
# _klaviyo_event call was failing 403 for a missing events:write scope. Every
# Klaviyo helper in store_api.py fails soft (a print, by design — a Klaviyo
# outage must never cost a sale), so it failed silently for a day.
#
# Scope status as probed 2026-08-04 against the key in $OVERRIDE_ENV:
#   events:write        PRESENT   (POST /api/events/ -> 400, not 403)
#   subscriptions:write PRESENT   (POST /api/profile-subscription-bulk-create-jobs/
#                                  -> 400 body error, not 403)
#
# Both are satisfied by a Full Access key created 2026-08-04. It replaced a clone
# that had failed to widen anything (see below), which had itself replaced the
# events-scoped key minted on 2026-08-02 — three keys in the env in three days,
# which is why this one is Full Access.
#
# Klaviyo will not let you edit an existing key's scopes, and —
# the part that cost an hour — the row's ⋮ > Clone action copies them verbatim
# with no opportunity to change anything. Cloning in order to "add a scope"
# silently yields a byte-for-byte-equivalent key, same name and all. The only
# path with a per-scope matrix is the "Create Private API Key" button.
#
# Beware its default if you go narrower than Full Access: a Custom Key starts at
# No Access for EVERY scope, so a key created to add Subscriptions will silently
# drop Events, List and Profiles unless you set all four. That would break
# _klaviyo_sync and _klaviyo_event — the two helpers that currently work — in
# exchange for fixing the one that does not.
#
# Probe rather than trust this comment; it goes stale the moment the key changes:
#   curl -s -o /dev/null -w '%{http_code}\n' -X POST \
#     https://a.klaviyo.com/api/profile-subscription-bulk-create-jobs/ \
#     -H "Authorization: Klaviyo-API-Key $KLAVIYO_API_KEY" -H 'revision: 2024-10-15' \
#     -H 'content-type: application/json' --data '{}'
# 403 = scope still missing; 400 = scope present, body rejected. Creates nothing
# either way. (The equivalent probe against /api/events/ does NOT share that
# property — a valid one creates a metric, and Klaviyo metrics cannot be
# deleted, so only ever probe events with a metric name you actually want.)
if grep -qhE '^KLAVIYO_API_KEY=.+' "$BRIDGR_ENV" "$OVERRIDE_ENV" 2>/dev/null; then
  echo "  present — profile sync (properties, list add/remove) will be ACTIVE"
  echo "  NOTE: presence does not prove scope. Run the probe in the comment above."
  if grep -qhE '^KLAVIYO_LIST_CONSENT=.+' "$BRIDGR_ENV" "$OVERRIDE_ENV" 2>/dev/null; then
    echo "  KLAVIYO_LIST_CONSENT overridden in env — verify it is single-opt-in with"
    echo "  NO flow triggers (NOT the trial or paid list; both trigger live"
    echo "  onboarding flows on Added to List)"
  elif grep -qE "KLAVIYO_LIST_CONSENT', '[A-Za-z0-9]+'" "$STORE_API"; then
    echo "  KLAVIYO_LIST_CONSENT using the built-in default (W7gYXU, single opt-in,"
    echo "  no flow triggers) — the checkout consent tick will be honoured"
  else
    echo "  !! No consent list configured. The checkout checkbox will render and"
    echo "  !! submit, and _klaviyo_subscribe will no-op — customers opt in and"
    echo "  !! stay NEVER_SUBSCRIBED:"
    echo "  !!     echo 'KLAVIYO_LIST_CONSENT=<list_id>' >> $OVERRIDE_ENV"
  fi
else
  echo "  NOT SET — trial/paid profiles will not reach Klaviyo and no lifecycle"
  echo "  email will ever send. Everything else works. To enable, add the key to"
  echo "  $OVERRIDE_ENV and re-run this script:"
  echo "      echo 'KLAVIYO_API_KEY=pk_live_...' >> $OVERRIDE_ENV"
fi

say "Restart $UNIT"
OLD_PID=$(systemctl show "$UNIT" -p MainPID --value)
echo "  old MainPID=$OLD_PID"
systemctl restart "$UNIT"
sleep 3
NEW_PID=$(systemctl show "$UNIT" -p MainPID --value)
echo "  new MainPID=$NEW_PID"
[ -n "$NEW_PID" ] && [ "$NEW_PID" != "0" ] && [ "$NEW_PID" != "$OLD_PID" ] || {
  echo "  !! service did not come back. journalctl -u $UNIT -n 40"; exit 1; }

say "Verify: confirm the new code is what got loaded"
# _send_trial_ending_email is this build's distinguishing feature, and note that
# the sense of that check is INVERTED from every previous version of this script.
# It used to assert the emailer was ABSENT — back when the day-27 notice had been
# handed to Klaviyo and a local copy would have double-sent. As of 2026-08-04 the
# send is deliberately back in _handle_trial_will_end, because the Klaviyo message
# is marketing-classified and therefore never reaches a customer who declined the
# checkout consent tick: they would be charged unwarned. So its presence is now
# the thing to confirm, and its absence means an old build is loaded.
#
# The duplicate risk that the old check guarded against is real but has moved to
# Klaviyo's side: message ReYNde (flow X2tesT, action 107908224) would otherwise
# send a second copy to a consented customer. It was set to Draft on 2026-08-04
# (verified by API read-back: action 107908224 reports status "draft"), so the
# store is now the only sender. That is a UI-only change — the public API exposes
# flow messages read-only — so this script cannot assert or restore it; the
# pairing rule in the rollback notes below is the only guard.
if grep -q KLAVIYO_API_KEY "$STORE_API" \
   && grep -q _owned_app_properties "$STORE_API" \
   && grep -q _klaviyo_event "$STORE_API" \
   && grep -q _klaviyo_subscribe "$STORE_API" \
   && grep -q "'subscription_status': 'trialing'" "$STORE_API" \
   && grep -q _send_trial_ending_email "$STORE_API" \
   && grep -q trial_notice_sent_for "$STORE_API" \
   && grep -q _cancel_reason_properties "$STORE_API" \
   && grep -q "metric='Lead Captured'" "$STORE_API"; then
  echo "  OK — Klaviyo sync + event emitter + consent grant + trialing reset present,"
  echo "       in-house day-27 emailer present with its idempotency claim column,"
  echo "       Stripe cancel-reason capture present (inert until the portal question is on),"
  echo "       inbound leads emit Lead Captured (inert until a flow is built on it)"
else
  echo "  !! loaded file is not the expected build"; exit 1
fi

# The greps above only describe what is ON DISK. gunicorn does not hot-reload,
# so a file newer than the running process means the workers are still serving
# the previous build — and /health returns 200 the whole time, cheerfully. This
# is the check the header comment calls decisive, so do it rather than describe
# it: on 2026-08-02 the service had been up since 16:09 UTC against a file
# written at 17:46, and nothing in this script would have caught it.
START_EPOCH=$(date -d "$(systemctl show "$UNIT" -p ActiveEnterTimestamp --value)" +%s)
MTIME_EPOCH=$(stat -c %Y "$STORE_API")
echo "  service started $(date -d "@$START_EPOCH" -u '+%F %T UTC'), code written $(date -d "@$MTIME_EPOCH" -u '+%F %T UTC')"
[ "$START_EPOCH" -ge "$MTIME_EPOCH" ] || {
  echo "  !! the running process is OLDER than the code on disk — restart did not pick it up"; exit 1; }
echo "  OK — process is newer than the file it imported"

say "Health checks"
echo -n "  direct  :$PORT/store-api/health   -> "; curl -s -o /dev/null -w "%{http_code}\n" "http://127.0.0.1:$PORT/store-api/health"
echo -n "  nginx   :80/store-api/health      -> "; curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1/store-api/health
echo -n "  /subscription-status (expect 401) -> "; curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1/store-api/subscription-status

say "Cleanup: remove redundant backup (identical to current file)"
rm -f "$STORE_DIR"/store_api.py.bak-20260731220228
echo "  done"

say "bridgr.service untouched"
systemctl is-active bridgr.service || true

echo
echo "Rollback if needed — the day-27 notice has TWO halves and this script owns only one."
echo
echo "  1. Code (here):"
echo "       cd $STORE_DIR && git checkout c203ec7 -- store_api.py && systemctl restart $UNIT"
echo "     c203ec7 = the build before the day-27 send moved back in-house. Rolling back"
echo "     also invalidates EXPECT_MD5 above, so this script refuses to run again until you"
echo "     restore the old sum 4e2d690e869dc97e0d03cff6202a220e — and its verify block"
echo "     asserts _send_trial_ending_email is ABSENT, so the two must be restored together."
echo
echo "     The DB column trial_notice_sent_for is left in place by a rollback and does no"
echo "     harm: nothing in c203ec7 reads it. Do NOT drop it — rolling forward again would"
echo "     otherwise re-race the migration for no reason."
echo
echo "  2. Klaviyo message ReYNde (flow X2tesT, action 107908224) — the OTHER half."
echo
echo "     READ THIS BEFORE ROLLING BACK. Exactly one of the two must be sending:"
echo "       ReYNde Live  + rolled-forward code = consented customers get the notice TWICE"
echo "       ReYNde Draft + rolled-back  code = NOBODY gets it, and every converting trial"
echo "                                          is charged with no warning at all"
echo "     ReYNde was set to Draft on 2026-08-04, so the SECOND row is the one you are"
echo "     one rollback away from. Set it back to Live as part of any code rollback —"
echo "     not afterwards. That row is the worse failure and it is silent: nothing"
echo "     errors, no log line appears, the charge simply lands unannounced."
echo "     Draft, not Manual: Manual still queues recipients for a human to release."
echo
echo "     Note what ReYNde alone cannot do, which is why the code moved in the first"
echo "     place: it is marketing-classified, so it only reaches profiles with marketing"
echo "     consent. Customers who declined the checkout tick are unreachable that way."
echo "     Rolling back accepts that gap; it does not fix it."
echo
echo "     UI only — https://www.klaviyo.com/flow/X2tesT/edit — the public API exposes"
echo "     flow messages read-only, so this cannot be scripted here."
echo
echo "  3. Unrelated to the above, still current: flow X2tesT's profile filter"
echo "       subscription_status not-equals 'cancelled'  OR  subscription_status not-set"
echo "     governs the MARKETING sequence, not the billing notice. Leave it alone for an"
echo "     ordinary rollback — both builds write subscription_status, so it keeps working."
