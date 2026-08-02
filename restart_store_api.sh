#!/usr/bin/env bash
#
# Restart-only deploy for pf9-store-api.service.
#
# Something root-side syncs /opt/pf9-store from the repo — NOT a GitHub Actions
# runner, despite what this comment used to claim: the only workflows in this
# repo are Pages and CodeQL. Confirm the tree is actually current before
# restarting — `git -C /opt/pf9-store diff HEAD origin/main` should be empty.
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
set -euo pipefail

STORE_DIR=/opt/pf9-store
STORE_API=$STORE_DIR/store_api.py
VENV=$STORE_DIR/venv
UNIT=pf9-store-api.service
PORT=5011
EXPECT_MD5=01e45e4187644ae68e9ce68d176310cd   # trial start writes subscription_status=trialing
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
if grep -qhE '^KLAVIYO_API_KEY=.+' "$BRIDGR_ENV" "$OVERRIDE_ENV" 2>/dev/null; then
  echo "  present — Klaviyo sync will be ACTIVE after this restart"
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
# The trialing marker is this build's distinguishing feature. It pairs with the
# Klaviyo-side day-27 profile filter (subscription_status not-equals cancelled
# OR not-set): without this write, a returning customer stays labelled
# 'cancelled' through their whole second trial.
if grep -q KLAVIYO_API_KEY "$STORE_API" \
   && grep -q _owned_app_properties "$STORE_API" \
   && grep -q _klaviyo_event "$STORE_API" \
   && grep -q "'subscription_status': 'trialing'" "$STORE_API" \
   && ! grep -q _send_trial_ending_email "$STORE_API"; then
  echo "  OK — Klaviyo sync + event emitter + trialing reset present, dup day-27 emailer gone"
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
echo "Rollback if needed:  cd $STORE_DIR && git checkout 12e1eef -- store_api.py && systemctl restart $UNIT"
echo "  (12e1eef = the build that was live before the subscription_status=trialing write."
echo "   Rolling back also means EXPECT_MD5 above no longer matches, so this script will"
echo "   refuse to run again until you restore the old sum f0e2b689c0249214803d6b2a81770809.)"
