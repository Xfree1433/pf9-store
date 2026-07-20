#!/usr/bin/env bash
#
# The /store-api repoint to :5011 is already written to /etc/nginx/sites-enabled/bridgr
# (previous run edited the file but aborted on an over-strict safety check before
# reloading). Confirm state and reload nginx. bridgr.service is NOT restarted.
#
# Run on xfree143 as:  sudo bash /tmp/reload_nginx_store_api.sh
#
set -euo pipefail
SITE=/etc/nginx/sites-enabled/bridgr
[ "$(id -u)" -eq 0 ] || { echo "must run as root (use sudo)"; exit 1; }

echo "=== current proxy targets ==="
grep -nE "location |proxy_pass http://127.0.0.1:501" "$SITE"

# /store-api block must be on :5011
if ! sed -n '/location \/store-api {/,/}/p' "$SITE" | grep -q "proxy_pass http://127.0.0.1:5011;"; then
  echo "!! /store-api is not on :5011; aborting."; exit 1
fi
# bridgr's own backends must still be :5010 (line '/' ends 5010; ; socket.io ends 5010/socket.io;)
BR=$(grep -c "proxy_pass http://127.0.0.1:5010" "$SITE" || true)
echo "  bridgr :5010 backends => $BR (expect 2)"
[ "$BR" -eq 2 ] || { echo "!! unexpected bridgr backend count; aborting."; exit 1; }

nginx -t
systemctl reload nginx

echo "=== VERIFY through nginx :80 ==="
echo -n "  /store-api/health              -> "; curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1/store-api/health
echo -n "  /store-api/subscription-status -> "; curl -s -w " (%{http_code})\n" http://127.0.0.1/store-api/subscription-status
echo "  (expect {\"error\":\"unauthorized\"} 401, NOT a 404 HTML page)"
echo "DONE. bridgr.service NOT restarted; only nginx reloaded."
