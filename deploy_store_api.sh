#!/usr/bin/env bash
#
# Split-service deploy for the PF9 store billing API.
# Goal: serve the NEW store_api.py (trials + /subscription-status) from its own
# systemd service on port 5011, and repoint nginx /store-api at it — WITHOUT
# touching or restarting bridgr.service.
#
# Run on xfree143 as:  sudo bash /tmp/deploy_store_api.sh
#
set -euo pipefail

STORE_DIR=/opt/pf9-store
STORE_API=$STORE_DIR/store_api.py
VENV=$STORE_DIR/venv
WSGI=$STORE_DIR/wsgi_store.py
OVERRIDE_ENV=$STORE_DIR/pf9-store-api.env
UNIT=/etc/systemd/system/pf9-store-api.service
BRIDGR_ENV=/opt/bridgr/.env
DB=/opt/bridgr/store_leads.db
NGINX_SITE=/etc/nginx/sites-available/bridgr
PORT=5011
EXPECT_MD5=24dc663f9c91d67bd85ac609ef5bcdf1   # 851221b-note commit — comment-only change

say(){ echo -e "\n=== $* ==="; }

# ── Preflight ───────────────────────────────────────────────────────────────
[ "$(id -u)" -eq 0 ] || { echo "must run as root (use sudo)"; exit 1; }
[ -f "$STORE_API" ] || { echo "missing $STORE_API"; exit 1; }
[ -f "$BRIDGR_ENV" ] || { echo "missing $BRIDGR_ENV"; exit 1; }
[ -f "$DB" ] || { echo "missing $DB"; exit 1; }
[ -f "$NGINX_SITE" ] || { echo "missing $NGINX_SITE"; exit 1; }

say "Preflight: verify store_api.py matches committed code"
GOT_MD5=$(md5sum "$STORE_API" | awk '{print $1}')
echo "  $STORE_API md5=$GOT_MD5 (expected $EXPECT_MD5)"
if [ "$GOT_MD5" != "$EXPECT_MD5" ]; then
  echo "  !! store_api.py on server does not match committed build; aborting."
  echo "  !! sync the committed file to $STORE_API first, then re-run."
  exit 1
fi

say "Preflight: port $PORT must be free"
if ss -ltn 2>/dev/null | grep -q ":$PORT "; then
  echo "  !! port $PORT already in use; aborting."; exit 1
fi

say "Preflight: nginx /store-api must currently proxy to :5010 exactly once"
CNT=$(grep -c "proxy_pass http://127.0.0.1:5010;" "$NGINX_SITE" || true)
echo "  matches for :5010 => $CNT"
[ "$CNT" -eq 1 ] || { echo "  !! expected exactly 1 occurrence; aborting for safety."; exit 1; }

DB_OWNER=$(stat -c '%U' "$DB")
DB_GROUP=$(stat -c '%G' "$DB")
echo "  store DB owned by $DB_OWNER:$DB_GROUP -> new service will run as that user"

# ── venv ────────────────────────────────────────────────────────────────────
say "Create dedicated venv + install deps (isolated from bridgr venv)"
if [ ! -x "$VENV/bin/python" ]; then
  python3 -m venv "$VENV"
fi
"$VENV/bin/pip" install --upgrade pip >/dev/null
# stripe is pinned deliberately. An unpinned install on 2026-07-20 pulled
# stripe 15.x, where StripeObject stopped being a dict subclass — every webhook
# handler calls .get() on the event object, so all of them began 500ing.
# store_api._plain() now normalises at the boundary so either major works, but
# the pin keeps a venv rebuild from silently changing the type again.
"$VENV/bin/pip" install flask gunicorn 'stripe==15.3.1' resend requests
chown -R "$DB_OWNER:$DB_GROUP" "$VENV"

# ── wsgi entrypoint ─────────────────────────────────────────────────────────
say "Write $WSGI"
cat > "$WSGI" <<'PYEOF'
import sys
sys.path.insert(0, '/opt/pf9-store')
from flask import Flask
from store_api import store_bp, init_db

app = Flask(__name__)
app.register_blueprint(store_bp)
init_db()
PYEOF
chown "$DB_OWNER:$DB_GROUP" "$WSGI"

# ── override env (the two new vars + explicit DB path) ───────────────────────
say "Write $OVERRIDE_ENV (loaded AFTER $BRIDGR_ENV so it wins)"
cat > "$OVERRIDE_ENV" <<EOF
# Store-API-only overrides. Loaded after /opt/bridgr/.env.
SUBSCRIPTION_STATUS_SECRET=wcjSY-J6pTKzQCiqseXGglATvEikZ6BSpAfoIg-e5VcrE5C0jZ_lImjMP2-68Y-l
TRIAL_PERIOD_DAYS=30
STORE_DB_PATH=$DB
EOF
chmod 600 "$OVERRIDE_ENV"
chown "$DB_OWNER:$DB_GROUP" "$OVERRIDE_ENV"

# ── systemd unit ────────────────────────────────────────────────────────────
say "Write $UNIT"
cat > "$UNIT" <<EOF
[Unit]
Description=PF9 Store billing API (split from bridgr)
After=network.target

[Service]
Type=simple
User=$DB_OWNER
Group=$DB_GROUP
WorkingDirectory=$STORE_DIR
EnvironmentFile=$BRIDGR_ENV
EnvironmentFile=$OVERRIDE_ENV
ExecStart=$VENV/bin/gunicorn --workers 2 --bind 127.0.0.1:$PORT wsgi_store:app
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

say "Enable + start pf9-store-api.service"
systemctl daemon-reload
systemctl enable pf9-store-api.service
systemctl restart pf9-store-api.service
sleep 2
systemctl --no-pager --full status pf9-store-api.service | head -n 12 || true

say "Local health check on :$PORT (before touching nginx)"
curl -fsS "http://127.0.0.1:$PORT/store-api/health" && echo || {
  echo "  !! new service not healthy on :$PORT; nginx NOT modified. Check: journalctl -u pf9-store-api -n 40"
  exit 1
}

# ── nginx repoint (reload, NOT a bridgr restart) ────────────────────────────
say "Back up + repoint nginx /store-api :5010 -> :$PORT"
cp -a "$NGINX_SITE" "${NGINX_SITE}.bak-$(date +%Y%m%d%H%M%S)"
sed -i "s#proxy_pass http://127.0.0.1:5010;#proxy_pass http://127.0.0.1:$PORT;#" "$NGINX_SITE"
nginx -t
systemctl reload nginx

# ── Verify through nginx ────────────────────────────────────────────────────
say "Verify through nginx (:80)"
echo -n "  /store-api/health          -> "; curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1/store-api/health
echo -n "  /store-api/subscription-status (no secret, expect 401/403 not 404) -> "
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1/store-api/subscription-status

say "DONE. bridgr.service was NOT restarted."
echo "  Store API now served by pf9-store-api.service on :$PORT."
echo "  Trials: 30-day (TRIAL_PERIOD_DAYS=30). SUBSCRIPTION_STATUS_SECRET set."
echo "  Rollback: restore ${NGINX_SITE}.bak-*, 'systemctl reload nginx', 'systemctl disable --now pf9-store-api'."
