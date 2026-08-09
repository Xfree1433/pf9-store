"""Drive the real /demo-request route and capture what would go to Klaviyo.

Every outbound call is stubbed: no email, no HubSpot, no Klaviyo. The DB is a
throwaway file. What we assert on is the exact properties payload.

    ./venv/bin/python tests/test_demo_endpoint.py

Exits non-zero on failure. These are not incidental checks — most of what they
assert is *absence*, and every one of those cases is silent in production if it
regresses: a fabricated first_name that poisons a customer's greeting forever, a
link in an outbound email built from a client-supplied string, prose chosen by a
stranger reaching an address the stranger also chose. None of it raises, none of
it shows up in a health check, and none of it is visible in the Klaviyo UI until
someone reads a delivered email.
"""
import os, sys, json, tempfile

os.environ['STORE_DB_PATH'] = tempfile.mktemp(suffix='.db')
os.environ['KLAVIYO_API_KEY'] = 'test-key-not-used'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import store_api

captured = []
store_api._send_notification = lambda *a, **k: None
store_api._hubspot_push_contact = lambda **k: None
store_api._klaviyo_event = lambda **k: captured.append(k)

store_api.init_db()

from flask import Flask
app = Flask(__name__)
app.register_blueprint(store_api.store_bp)
client = app.test_client()

fails = []


def post(body, referer=None, label=''):
    del captured[:]
    headers = {'Referer': referer} if referer else {}
    r = client.post('/store-api/demo-request', json=body, headers=headers)
    return r, (captured[0] if captured else None)


def expect(label, cond, detail=''):
    print(f'  {"ok " if cond else "FAIL"}  {label}{("  — " + detail) if detail and not cond else ""}')
    if not cond:
        fails.append(label)


print('=== contact.html: a real question ===')
r, ev = post({'name': 'Dana Reyes', 'email': 'Dana@Example.COM', 'company': 'Reyes Mfg',
              'product': 'SHIFTLOG', 'message': 'Does it export to CSV?'},
             referer='https://store.plainspokenfoundrynine.com/contact.html?utm_source=x&email=leak@x.com')
p = (ev or {}).get('properties', {})
print('   ', json.dumps(p, sort_keys=True))
expect('200 OK', r.status_code == 200)
expect('metric is Lead Captured', (ev or {}).get('metric') == 'Lead Captured')
expect('lead_type=question', p.get('lead_type') == 'question')
expect('product set (in PRICE_MAP)', p.get('product') == 'SHIFTLOG')
expect('vertical=manufacturing', p.get('vertical') == 'manufacturing')
expect('company carried', p.get('company') == 'Reyes Mfg')
expect('has_question=True', p.get('has_question') is True)
expect('source_page is path only', p.get('source_page') == '/contact.html')
expect('NO query string anywhere in payload', 'leak@x.com' not in json.dumps(p))
expect('question text NOT forwarded', 'CSV' not in json.dumps(p))
expect('unique_id is the row id', (ev or {}).get('unique_id') == 'lead-1')
expect('real name passed through for first/last split', (ev or {}).get('name') == 'Dana Reyes')

print()
print('=== a synthesised name must never reach the profile ===')
for nm, em, want in [
    ('j.smith',   'j.smith@example.com',   None),          # what 7 of 8 surfaces send
    ('J.Smith',   'j.smith@example.com',   None),          # case must not defeat it
    (' dana ',    'dana@example.com',      None),          # whitespace must not defeat it
    ('Dana Reyes','dana@example.com',      'Dana Reyes'),  # a real name survives
    ('Dana',      'notthesame@example.com','Dana'),
]:
    r, ev = post({'name': nm, 'email': em, 'company': '', 'product': 'SHIFTLOG', 'message': 'q'})
    # Assert the event FIRED before asserting what is on it — otherwise a 400
    # that captures nothing reads as "name suppressed" and passes for the wrong
    # reason. (It did, on the blank-name case, until this line was added.)
    expect(f'name={nm!r:12} email={em:24} fired', r.status_code == 200 and ev is not None)
    got = (ev or {}).get('name')
    expect(f'name={nm!r:12} email={em:24} -> {want!r}', got == want, f'got {got!r}')

# A blank name is rejected upstream at store_api.py:932 and never reaches Klaviyo
# or the DB at all. Asserted explicitly so the suite states which mechanism ran.
r = client.post('/store-api/demo-request',
                json={'name': '', 'email': 'blank@example.com', 'product': 'SHIFTLOG'})
expect('blank name is a 400, not a silent suppression', r.status_code == 400, f'got {r.status_code}')

print()
# As of 2026-08-09 no card sends a waitlist lead — FIELDVIEWR and MARKUPR were the
# last two and both flipped to Subscribe. This block is now a SERVER-CONTRACT test,
# not a description of live traffic: openWaitlist() is still defined for the next
# unreleased app, and rows in this shape already exist in store_leads.db, so the
# parsing must keep working. Don't delete it because "nothing sends this".
print('=== waitlist-shaped lead: suffixed tag is not sellable ===')
r, ev = post({'name': 'sam', 'email': 'sam@example.com', 'company': '',
              'product': 'MARKUPR (waitlist)', 'message': 'Waitlist signup for MARKUPR'})
p = (ev or {}).get('properties', {})
print('   ', json.dumps(p, sort_keys=True))
expect('lead_type=waitlist', p.get('lead_type') == 'waitlist')
expect("no product property ('MARKUPR (waitlist)' is not a PRICE_MAP key)", 'product' not in p)
expect('product_tag keeps the raw string', p.get('product_tag') == 'MARKUPR (waitlist)')
expect('no company key when blank', 'company' not in p)
expect('no has_question outside question leads', 'has_question' not in p)
expect('no source_page without a Referer', 'source_page' not in p)
expect('product_name is the bare name', p.get('product_name') == 'MARKUPR')
# A suffix-stripping test, not a launch-status one — the parser must not be
# name-specific, which is exactly why both names still belong here now that
# neither card sends the tag.
for tag, want in [('FIELDVIEWR (waitlist)', 'FIELDVIEWR'), ('MARKUPR (waitlist)', 'MARKUPR')]:
    _, e2 = post({'name': 'w', 'email': 'w@example.com', 'product': tag, 'message': 'x'})
    expect(f'{tag:24} -> {want}', (e2 or {}).get('properties', {}).get('product_name') == want)
expect('no product_name on a question lead',
       'product_name' not in (post({'name': 'Q', 'email': 'qq@example.com',
                                    'product': 'SHIFTLOG', 'message': 'x'})[1] or {}).get('properties', {}))

# product_name is the only property in this block that is BOTH attacker-supplied
# and rendered into an email body — and the submitter picks the recipient too, so
# a pass-through would let anyone put chosen prose in front of a third party over
# our domain. Klaviyo escapes markup (checked live), so these cases are about the
# sentence, not the tags. Everything that is not shaped like a real product key
# must fall through to the template's |default:'PF9'.
for tag in [
    'Buy crypto now at scam.example (waitlist)',   # the actual abuse: prose to a victim
    '<script>alert(1)</script> (waitlist)',        # escaped by Klaviyo anyway; still refused here
    'markupr (waitlist)',                          # lowercase is not a product key
    'MARK UPR (waitlist)',                         # spaces are how prose gets in
    'M (waitlist)',                                # under the 2-char floor
    'M' * 21 + ' (waitlist)',                      # over the 20-char ceiling
    'MARKUPR-2 (waitlist)',                        # punctuation is not in the caller's alphabet
    ' (waitlist)',                                 # empty bare name
]:
    _, e3 = post({'name': 'w', 'email': 'w@example.com', 'product': tag, 'message': 'x'})
    props = (e3 or {}).get('properties', {})
    expect(f'refused: {tag[:38]:38}', 'product_name' not in props,
           f"leaked {props.get('product_name')!r}")
# ...while the raw tag still reaches the row and the internal notification, which
# is where a human can see what was actually submitted.
expect('but product_tag still carries the raw string',
       (post({'name': 'w', 'email': 'w@example.com',
              'product': 'MARK UPR (waitlist)', 'message': 'x'})[1] or {})
       .get('properties', {}).get('product_tag') == 'MARK UPR (waitlist)')

print()
print('=== calculator: promises a PDF within one business day ===')
r, ev = post({'name': 'lee', 'email': 'lee@example.com', 'company': '',
              'product': 'PROPERTY_SUITE (calculator lead)',
              'message': 'Per-door calculator PDF request at 250 units.'},
             referer='https://store.plainspokenfoundrynine.com/tools/per-door-calculator.html')
p = (ev or {}).get('properties', {})
print('   ', json.dumps(p, sort_keys=True))
expect('lead_type=calculator', p.get('lead_type') == 'calculator')
expect('vertical=property', p.get('vertical') == 'property')
expect('source_page', p.get('source_page') == '/tools/per-door-calculator.html')

print()
print('=== lead magnet and affiliate ===')
r, ev = post({'name': 'x', 'email': 'x@example.com', 'company': '',
              'product': 'MANUFACTURING_LEAD_MAGNET (NCR-CAPA Log)', 'message': 'download'})
p = (ev or {}).get('properties', {})
expect('lead_type=lead_magnet', p.get('lead_type') == 'lead_magnet')
expect('vertical=manufacturing', p.get('vertical') == 'manufacturing')
expect('lead_magnet_name resolved', p.get('lead_magnet_name') == 'NCR / CAPA Log Template')
expect('lead_magnet_url resolved', p.get('lead_magnet_url') ==
       'https://store.plainspokenfoundrynine.com/templates/ncr-capa-log-template.html')

r, ev = post({'name': 'y', 'email': 'y@example.com', 'company': '',
              'product': 'AFFILIATE_PROGRAM_SIGNUP', 'message': 'plan'})
p = (ev or {}).get('properties', {})
expect('lead_type=affiliate', p.get('lead_type') == 'affiliate')
expect('no vertical for affiliate', 'vertical' not in p or p['vertical'] is None)

print()
print('=== every lead magnet resolves, and only to a URL we wrote ===')
import store_api as _sa
for tag, (want_name, want_url) in _sa._LEAD_MAGNET_ASSETS.items():
    r, ev = post({'name': 'm', 'email': 'm@example.com', 'company': '',
                  'product': tag, 'message': 'download request'})
    p = (ev or {}).get('properties', {})
    expect(f'{tag[:34]:34} -> url', p.get('lead_magnet_url') == want_url, str(p.get('lead_magnet_url')))
    expect(f'{tag[:34]:34} -> name', p.get('lead_magnet_name') == want_name)
    expect(f'{tag[:34]:34} is lead_magnet', p.get('lead_type') == 'lead_magnet')
    expect(f'{tag[:34]:34} url is on our host',
           want_url.startswith('https://store.plainspokenfoundrynine.com/templates/'))

# A tag that looks like a magnet but is not in the table must produce NO link.
r, ev = post({'name': 'm', 'email': 'm@example.com', 'company': '',
              'product': 'MANUFACTURING_LEAD_MAGNET (Evil ../../etc/passwd)', 'message': 'x'})
p = (ev or {}).get('properties', {})
expect('unknown magnet still classified', p.get('lead_type') == 'lead_magnet')
expect('unknown magnet writes NO url', 'lead_magnet_url' not in p)
expect('unknown magnet writes NO name', 'lead_magnet_name' not in p)
expect('no lead_magnet_url on a non-magnet lead',
       'lead_magnet_url' not in (post({'name': 'n', 'email': 'n@example.com',
                                       'product': 'SHIFTLOG', 'message': 'hi'})[1] or {}).get('properties', {}))

print()
print('=== calculator size: the number, never the prose ===')
for msg, want_size, want_unit in [
    ('Per-door calculator PDF request at 250 units.', 250, 'units'),
    ('Per-user calculator PDF request at 40 users.',   40,  'users'),
    ('Per-door calculator PDF request at 1 units.',     1,  'units'),
    ('Per-door calculator PDF request at 9999999 units.', 9999999, 'units'),
]:
    r, ev = post({'name': 'c', 'email': 'c@example.com', 'company': '',
                  'product': 'PROPERTY_SUITE (calculator lead)', 'message': msg})
    p = (ev or {}).get('properties', {})
    expect(f'{msg[:44]:44} -> {want_size}', p.get('calculator_size') == want_size, str(p.get('calculator_size')))
    expect(f'{msg[:44]:44} -> {want_unit}', p.get('calculator_unit') == want_unit)
    expect(f'{msg[:44]:44} size is an int', isinstance(p.get('calculator_size'), int))
    expect(f'{msg[:44]:44} sentence itself not forwarded', msg not in json.dumps(p))
    expect(f'{msg[:44]:44} no "PDF request" prose', 'PDF request' not in json.dumps(p))

for bad in ['', 'no number here', 'at 12345678 units.', 'at zero units.',
            'at 250 doors.', 'Per-door calculator PDF request at units.']:
    r, ev = post({'name': 'c', 'email': 'c@example.com', 'company': '',
                  'product': 'PROPERTY_SUITE (calculator lead)', 'message': bad})
    p = (ev or {}).get('properties', {})
    expect(f'no size from {bad[:30]!r:34}', 'calculator_size' not in p, str(p.get('calculator_size')))
    expect(f'no unit from {bad[:30]!r:34}', 'calculator_unit' not in p)

expect('no calculator_size on a question lead',
       'calculator_size' not in (post({'name': 'q2', 'email': 'q2@example.com', 'product': 'COMPLI',
                                       'message': 'we have at 250 units of stock'})[1] or {}).get('properties', {}))

print()
print('=== whitespace-only product must not write an empty property ===')
r, ev = post({'name': 'z', 'email': 'z@example.com', 'company': '',
              'product': '     ', 'message': ''})
p = (ev or {}).get('properties', {})
print('   ', json.dumps(p, sort_keys=True))
expect('still 200', r.status_code == 200)
expect('no empty product_tag', p.get('product_tag', 'MISSING') != '')
expect('falls back to question', p.get('lead_type') == 'question')

print()
print('=== a Klaviyo failure must not cost us the lead ===')
def boom(**k):
    raise RuntimeError('Klaviyo down')
store_api._klaviyo_event = boom
import sqlite3
def _rows():
    return sqlite3.connect(os.environ['STORE_DB_PATH']).execute(
        'SELECT COUNT(*) FROM demo_requests').fetchone()[0]
# Measured as a DELTA, not against a hardcoded total. The absolute count was
# `n == 31` and broke the moment cases were added above — which is a test that
# fails for a reason having nothing to do with what it claims to check. What is
# actually being asserted is that a Klaviyo outage still leaves the lead in our
# own DB, and that is a difference of exactly one.
before = _rows()
r = client.post('/store-api/demo-request',
                json={'name': 'q', 'email': 'q@example.com', 'product': 'COMPLI'})
expect('visitor still gets 200', r.status_code == 200, f'got {r.status_code}')
expect('success true', (r.get_json() or {}).get('success') is True)
after = _rows()
expect('row still persisted despite the Klaviyo failure', after == before + 1,
       f'{before} -> {after}')

print()
print('=== rows written are unchanged in shape ===')
row = sqlite3.connect(os.environ['STORE_DB_PATH']).execute(
    'SELECT name, email, product FROM demo_requests ORDER BY id LIMIT 1').fetchone()
expect('first row intact', row == ('Dana Reyes', 'Dana@Example.COM', 'SHIFTLOG'), str(row))

os.unlink(os.environ['STORE_DB_PATH'])
print()
if fails:
    print('FAILURES:', fails)
    sys.exit(1)
print('all endpoint checks passed')
