#!/usr/bin/env bash
#
# The LOADED nginx site is /etc/nginx/sites-enabled/bridgr (a real file, NOT a
# symlink to sites-available). It still routes /store-api -> :5010 (old bridgr
# store code). Repoint ONLY the /store-api block to :5011 (the new
# pf9-store-api.service). bridgr's own '/' and '/socket.io' stay on :5010 and
# are NOT modified. bridgr.service is NOT restarted; nginx is only reloaded.
#
# Run on xfree143 as:  sudo bash /tmp/fix_nginx_store_api.sh
#
set -euo pipefail
SITE=/etc/nginx/sites-enabled/bridgr
PORT=5011

[ "$(id -u)" -eq 0 ] || { echo "must run as root (use sudo)"; exit 1; }
[ -f "$SITE" ] || { echo "missing $SITE"; exit 1; }
grep -q "location /store-api" "$SITE" || { echo "no /store-api block in $SITE; aborting"; exit 1; }

echo "=== BEFORE: proxy targets ==="
grep -nE "location |proxy_pass http://127.0.0.1:501" "$SITE"

cp -a "$SITE" "${SITE}.bak-$(date +%Y%m%d%H%M%S)"

# Scoped replace: only within the '/store-api { ... }' block (line of the
# location up to the first closing brace). bridgr's other blocks are untouched.
sed -i "/location \/store-api {/,/}/ s#proxy_pass http://127.0.0.1:5010;#proxy_pass http://127.0.0.1:$PORT;#" "$SITE"

echo "=== AFTER: proxy targets (expect /store-api -> :$PORT, others still :5010) ==="
grep -nE "location |proxy_pass http://127.0.0.1:501" "$SITE"

# Safety: bridgr's own routes must still point at :5010
BR=$(grep -c "proxy_pass http://127.0.0.1:5010;" "$SITE" || true)
echo "  bridgr :5010 backends remaining => $BR (expect 2: '/' and '/socket.io')"
[ "$BR" -eq 2 ] || { echo "  !! unexpected bridgr backend count; review before reload."; exit 1; }

nginx -t
systemctl reload nginx

echo "=== VERIFY through nginx :80 ==="
echo -n "  /store-api/health              -> "; curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1/store-api/health
echo -n "  /store-api/subscription-status -> "; curl -s -w " (%{http_code})\n" http://127.0.0.1/store-api/subscription-status
echo "  (subscription-status should now be {\"error\":\"unauthorized\"} 401, NOT a 404 HTML page)"
echo "DONE. bridgr.service NOT restarted; only nginx reloaded."
