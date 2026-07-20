#!/usr/bin/env bash
#
# Cleanup: a backup file was left inside /etc/nginx/sites-enabled/ (bridgr.bak-*).
# nginx loads EVERY file in sites-enabled/, so that stale copy became a SECOND
# ':80 server_name _' block routing /store-api -> :5010 (the "conflicting server
# name _" warning). Move all such backups OUT of sites-enabled/ so only the live
# 'bridgr' file remains. bridgr.service is NOT restarted; nginx only reloaded.
#
# Run on xfree143 as:  sudo bash /tmp/cleanup_nginx_bak.sh
#
set -euo pipefail
[ "$(id -u)" -eq 0 ] || { echo "must run as root (use sudo)"; exit 1; }
DEST=/etc/nginx/_disabled-backups
mkdir -p "$DEST"

echo "=== backups currently polluting sites-enabled/ ==="
ls -la /etc/nginx/sites-enabled/bridgr.bak-* 2>/dev/null || echo "  (none)"

shopt -s nullglob
moved=0
for f in /etc/nginx/sites-enabled/bridgr.bak-* /etc/nginx/sites-enabled/*.bak-*; do
  [ -e "$f" ] || continue
  mv -v "$f" "$DEST/"
  moved=$((moved+1))
done
echo "  moved $moved file(s) to $DEST"

echo "=== live sites-enabled/ now ==="
ls -la /etc/nginx/sites-enabled/

echo "=== config test (expect NO 'conflicting server name' warning) ==="
nginx -t
systemctl reload nginx

echo "=== VERIFY (production Host: app.plainspokenfoundrynine.com) ==="
H='Host: app.plainspokenfoundrynine.com'
echo -n "  /store-api/health              -> "; curl -s -o /dev/null -w "%{http_code}\n" -H "$H" http://127.0.0.1/store-api/health
echo -n "  /store-api/subscription-status -> "; curl -s -w " (%{http_code})\n" -H "$H" http://127.0.0.1/store-api/subscription-status | head -c 120; echo
echo -n "  bridgr root '/'                -> "; curl -s -o /dev/null -w "%{http_code}\n" -H "$H" http://127.0.0.1/
echo "  (want: health 200, subscription-status 401, bridgr / 200 or 302 — bridgr intact)"
echo "DONE. bridgr.service NOT restarted; only nginx reloaded."
