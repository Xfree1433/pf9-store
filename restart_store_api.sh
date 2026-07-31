#!/usr/bin/env bash
#
# Restart-only deploy for pf9-store-api.service.
#
# The GitHub Actions runner already syncs /opt/pf9-store on push, but gunicorn
# does not hot-reload — the running workers keep serving whatever code they
# imported at start. This restarts them, with guards so a bad file or a missing
# secret is caught before the service goes down rather than after.
#
# Run on xfree143 as:  ssh -t xfree143.taile2beaa.ts.net 'sudo bash /tmp/restart_store_api.sh'
#
set -euo pipefail

STORE_DIR=/opt/pf9-store
STORE_API=$STORE_DIR/store_api.py
VENV=$STORE_DIR/venv
UNIT=pf9-store-api.service
PORT=5011
EXPECT_MD5=c3d9bd0de2dcb90ea008b1f5b2b27016
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
if grep -q KLAVIYO_API_KEY "$STORE_API" && ! grep -q _send_trial_ending_email "$STORE_API"; then
  echo "  OK — Klaviyo sync present, duplicate day-27 emailer gone"
else
  echo "  !! loaded file is not the expected build"; exit 1
fi

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
echo "Rollback if needed:  cd $STORE_DIR && git checkout 23cde47 -- store_api.py && systemctl restart $UNIT"
