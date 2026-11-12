#!/usr/bin/env python3
"""Probe every PF9 service and write status.json for status.html.

Run by .github/workflows/status.yml on a schedule, from GitHub's network, so
the result does not depend on any PF9 server being up. Standard library only.

A service is:
  operational  - its health URL answered 200 with the expected JSON
  degraded     - it answered 200 but reports a problem (e.g. database not
                 connected), or only answered on the second attempt
  down         - no acceptable answer in two attempts (timeout, 5xx, a
                 redirect to a login page, non-JSON, ...)

The output deliberately carries no URLs, error text or response bodies: the
file is public. Details go to the workflow log instead.
"""
import json
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

DOMAIN = "plainspokenfoundrynine.com"
TIMEOUT = 12          # seconds per attempt
RETRY_PAUSE = 5       # seconds before the second attempt

# (group, display name, host, path, kind)
#   kind "health"  -> expects 200 + a JSON object
#   kind "page"    -> expects 200 + an HTML page containing `needle`
SERVICES = [
    ("Manufacturing", "FLOWTRACK", "flowtrack", "/api/health", "health"),
    ("Manufacturing", "QUALIFI", "qualifi", "/api/health", "health"),
    ("Manufacturing", "SHIFTLOG", "shiftlog", "/api/health", "health"),
    ("Manufacturing", "REPORTR", "reportr", "/api/health", "health"),
    ("Manufacturing", "INSPECTR", "inspectr", "/api/health", "health"),
    ("Property Management", "LANDLORDR", "landlordr", "/api/health", "health"),
    ("Property Management", "TENANTLINK", "tenantlinkr", "/api/health", "health"),
    ("Operations & AI", "PERMITR", "permitr", "/api/health", "health"),
    ("Operations & AI", "TASKFLOW", "taskflow", "/api/health", "health"),
    ("Operations & AI", "OPSIQ", "opsiq", "/api/health", "health"),
    ("Operations & AI", "EXTRACTR", "extractr", "/api/health", "health"),
    ("Operations & AI", "SUPPORTR", "supportr", "/api/health", "health"),
    ("Operations & AI", "MAINTAINR", "maintainr", "/api/health", "health"),
    ("Operations & AI", "COMPLI", "compli", "/api/health", "health"),
    ("Operations & AI", "MARKUPR", "markupr", "/api/health", "health"),
    ("Operations & AI", "FIELDVIEWR", "fieldviewr", "/api/health", "health"),
    ("Events", "SHOWJUDGR", "showjudgr", "/api/health", "health"),
    ("Store", "Storefront", "store", "/", "page"),
    ("Store", "Checkout & billing", "app", "/store-api/health", "health"),
]
PAGE_NEEDLE = "Plainspoken Foundry Nine"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """A redirect is a failure here: a health URL that bounces to a login
    page must not be followed to that page's 200."""

    def redirect_request(self, *a, **k):
        return None


_opener = urllib.request.build_opener(_NoRedirect)


def _reports_problem(body):
    """True when a health JSON object itself says something is wrong."""
    db = body.get("database")
    if isinstance(db, str) and db.lower() != "connected":
        return True
    status = body.get("status")
    if isinstance(status, str) and status.lower() not in ("ok", "healthy", "up"):
        return True
    if body.get("ok") is False:
        return True
    return False


def probe_once(url, kind):
    """Return (state, detail). state is 'operational' | 'degraded' | 'down'."""
    req = urllib.request.Request(
        url, headers={"User-Agent": "PF9-StatusCheck/1.0", "Cache-Control": "no-cache"}
    )
    try:
        with _opener.open(req, timeout=TIMEOUT) as resp:
            code = resp.status
            raw = resp.read(200_000)
    except urllib.error.HTTPError as exc:
        return "down", f"HTTP {exc.code}"
    except Exception as exc:  # timeout, DNS, TLS, connection reset
        return "down", type(exc).__name__
    if code != 200:
        return "down", f"HTTP {code}"
    text = raw.decode("utf-8", "replace")
    if kind == "page":
        return ("operational", "ok") if PAGE_NEEDLE in text else ("down", "unexpected page")
    try:
        body = json.loads(text)
    except ValueError:
        return "down", "200 but not JSON"
    if not isinstance(body, dict):
        return "down", "200 but not a JSON object"
    if _reports_problem(body):
        return "degraded", "health reports a problem"
    return "operational", "ok"


def probe(service):
    group, name, host, path, kind = service
    url = f"https://{host}.{DOMAIN}{path}"
    started = time.monotonic()
    state, detail = probe_once(url, kind)
    if state == "down":
        time.sleep(RETRY_PAUSE)
        started = time.monotonic()
        state2, detail2 = probe_once(url, kind)
        if state2 != "down":
            # Answered on the retry: reachable, but not cleanly.
            state, detail = "degraded", f"first attempt failed ({detail}); retry {detail2}"
        else:
            detail = f"{detail}; retry {detail2}"
    ms = int((time.monotonic() - started) * 1000)
    print(f"{name:<20} {state:<12} {ms:>6} ms  {url}  {detail}", file=sys.stderr)
    return {"group": group, "name": name, "status": state}


def main(out_path):
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(probe, SERVICES))
    doc = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "services": results,
    }
    with open(out_path, "w") as fh:
        json.dump(doc, fh, indent=1)
        fh.write("\n")
    down = sum(r["status"] == "down" for r in results)
    print(f"wrote {out_path}: {len(results)} services, {down} down", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "status.json")
