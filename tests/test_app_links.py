"""Check _app_link_properties against every product the store can sell.

    ./venv/bin/python tests/test_app_links.py            # offline, no network
    ./venv/bin/python tests/test_app_links.py --live     # also HTTP-checks each URL

Exits non-zero on failure.

These two properties are hrefs in live emails, so the failure mode is not an
exception — it is a customer clicking "Log in to <app>" and landing on a 404.
The offline half asserts the shape and the no-stale-value rule; --live asserts
the URLs actually resolve, which is the only check that catches an app moving
its login page.
"""
import os, sys

os.environ.setdefault('KLAVIYO_API_KEY', '')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from store_api import (_app_link_properties, _onboarding_properties,
                       APP_LOGIN_PATH, APP_TEAM_PATH, ONBOARDING_COPY,
                       APP_URL_MAP, BUNDLE_MAP, PRICE_MAP, STORE_URL)

fails = []


def expect(label, ok, detail=''):
    if not ok:
        fails.append(f'{label}{": " + detail if detail else ""}')
    print(f'  {"ok " if ok else "FAIL"}  {label}{"" if ok else "  <- " + detail}')


print('=== both keys are always present, for every sellable product ===')
# The absence assertion is the whole point. These are profile properties, so a
# missing key does not fall back to the template default — it leaves whatever
# the customer's PREVIOUS app wrote. Someone who trials FLOWTRACK then converts
# SUPPORTR would get a SUPPORTR email linking into FLOWTRACK.
for product in sorted(PRICE_MAP):
    props = _app_link_properties(product)
    expect(f'{product:<18} emits both keys',
           set(props) == {'app_login_url', 'add_team_url'}, repr(sorted(props)))
    for k, v in props.items():
        expect(f'{product:<18} {k} is a non-empty https URL',
               isinstance(v, str) and v.startswith('https://'), repr(v))

print()
print('=== unknown products degrade to the store, never to empty ===')
for product in ['', None, 'NOPE', 'PROPERTY_BUNDLE', '../etc/passwd']:
    props = _app_link_properties(product)
    expect(f'{str(product):<18} both keys = STORE_URL',
           props == {'app_login_url': STORE_URL, 'add_team_url': STORE_URL},
           repr(props))

print()
print('=== the two maps only ever name products we actually have hosts for ===')
# A key here with no APP_URL_MAP entry would silently produce a store link while
# looking, in the source, like it had been handled.
for name, m in [('APP_LOGIN_PATH', APP_LOGIN_PATH), ('APP_TEAM_PATH', APP_TEAM_PATH)]:
    for product in m:
        expect(f'{name}[{product}] has a host', product in APP_URL_MAP)
        expect(f'{name}[{product}] is sellable', product in PRICE_MAP)

# ...and the converse, which is the one that catches drift rather than typos.
# Adding an app to APP_URL_MAP without a login path is not an error and raises
# nothing — it just quietly sends that app's trialists to the storefront from a
# button that offered to log them in, which is the exact bug this whole change
# exists to fix. A team path is genuinely optional (nine products have no such
# page), so only the login side is required.
for product in APP_URL_MAP:
    expect(f'APP_URL_MAP[{product}] has a login path too', product in APP_LOGIN_PATH,
           'new app added without one -> silent storefront link')

print()
print('=== an empty login path means the ROOT, and must not lose the host ===')
# QUALIFI / INSPECTR / OPSIQ map to '' deliberately: their root IS the sign-in
# screen. `if login_path` instead of `if login_path is not None` would treat
# that as "unmapped" and send all three to the storefront — a falsy-vs-missing
# bug that no exception would ever report.
for product in [p for p, v in APP_LOGIN_PATH.items() if v == '']:
    got = _app_link_properties(product)['app_login_url']
    expect(f'{product:<18} login url is its own host root',
           got == APP_URL_MAP[product].rstrip('/'), repr(got))

print()
print('=== EVERY sellable product has all eight copy keys ===')
# Full coverage, not "eight or zero", and the difference matters. These are
# profile properties, so an uncovered product does not fall back to the
# template default — it keeps whatever the customer's PREVIOUS app wrote. Since
# checkout rejects anything outside PRICE_MAP, covering PRICE_MAP is what makes
# it impossible for one product's onboarding copy to appear under another's name.
#
# A partial set is the other bad shape: Trial Day 1 renders step 1 and step 2
# side by side, so half a set puts an app-specific instruction next to the
# generic default, which reads as a mistake in a way neither version does alone.
EIGHT = {f'{p}_{s}' for p in ('onboarding_step1', 'onboarding_step2',
                              'day3_feature', 'month1_feature')
         for s in ('title', 'detail')}
for product in sorted(PRICE_MAP):
    props = _onboarding_properties(product)
    expect(f'{product:<18} has all eight keys', set(props) == EIGHT, repr(sorted(props)))
    for k, v in sorted(props.items()):
        expect(f'{product:<18} {k} is real prose',
               isinstance(v, str) and len(v.strip()) > 3 and v == v.strip(), repr(v))

print()
print('=== unsellable products get nothing (and cannot reach checkout anyway) ===')
for product in ['', None, 'NOPE', '../etc/passwd']:
    expect(f'{str(product):<18} -> {{}}', _onboarding_properties(product) == {})

print()
print('=== the copy table only names products we actually sell ===')
for product in ONBOARDING_COPY:
    expect(f'ONBOARDING_COPY[{product}] is sellable', product in PRICE_MAP)

print()
print('=== no product borrows another product\'s onboarding copy ===')
# Copy-paste across fifteen entries is the realistic way this table goes wrong,
# and a duplicated detail would ship a LANDLORDR instruction to a COMPLI trial
# without erroring.
seen_detail = {}
for product, copy in ONBOARDING_COPY.items():
    for slot, (title, detail) in copy.items():
        prev = seen_detail.get(detail)
        expect(f'{product}.{slot} detail is not a duplicate of {prev}', prev is None)
        seen_detail[detail] = f'{product}.{slot}'

print()
print('=== copy never names an app the customer did not buy ===')
# The one substantive error this table can make that still reads fluently:
# telling a SHIFTLOG customer to open a FLOWTRACK screen. Product names are
# uppercase and distinctive, so this is cheap to check.
#
# A bundle may name the apps it contains — PROPERTY_BUNDLE's copy has to say
# "set up LANDLORDR first, then invite the tenant into TENANTLINK", because
# that is what the customer bought and the order genuinely matters. The
# allowance comes from BUNDLE_MAP rather than an exception list, so adding a
# bundle later does not need this test edited, and mis-naming an app that is
# NOT in the bundle still fails.
for product, copy in ONBOARDING_COPY.items():
    blob = ' '.join(t + ' ' + d for t, d in copy.values())
    owned = {product} | set(BUNDLE_MAP.get(product, []))
    for other in set(PRICE_MAP) - owned:
        expect(f'{product} copy does not mention {other}', other not in blob)

if '--live' in sys.argv:
    import urllib.request, urllib.error
    print()
    print('=== every emitted URL resolves (no 404s in a live email) ===')
    seen = set()
    for product in sorted(PRICE_MAP):
        for k, url in sorted(_app_link_properties(product).items()):
            if url in seen:
                continue
            seen.add(url)
            req = urllib.request.Request(url, method='GET',
                                         headers={'User-Agent': 'pf9-link-check'})
            try:
                code = urllib.request.urlopen(req, timeout=20).status
            except urllib.error.HTTPError as e:
                code = e.code
            except Exception as e:                      # DNS, TLS, timeout
                code = f'ERR {type(e).__name__}'
            # A redirect to the app's own login is a pass: most of these are
            # behind auth, and being asked to sign in is the intended landing.
            # Only 404/410/5xx and transport errors are failures.
            ok = code in (200, 301, 302, 303, 307, 308)
            expect(f'{str(code):<6} {url}', ok)
else:
    print()
    print('(skipping live URL checks; re-run with --live to HTTP-check every link)')

print()
if fails:
    print('FAILURES:')
    for f in fails:
        print('  -', f)
    sys.exit(1)
print('all app-link checks passed')
