"""Check _lead_type_for / _lead_vertical_for against every product tag the
front-end actually sends, plus the 15 tags already in the production DB.

    ./venv/bin/python tests/test_lead_event.py

Exits non-zero on failure. lead_type is the branch key for the whole Lead
Captured flow, so a tag that classifies wrong does not error — it just sends
somebody the wrong email.
"""
import os, sys

os.environ.setdefault('KLAVIYO_API_KEY', '')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from store_api import (_lead_type_for, _lead_vertical_for,
                       _hubspot_list_for_product, PRICE_MAP,
                       HUBSPOT_LIST_MANUFACTURING, HUBSPOT_LIST_PROPERTY)

fails = []


def check(label, got, want):
    ok = got == want
    if not ok:
        fails.append(f'{label}: got {got!r}, want {want!r}')
    print(f'  {"ok " if ok else "FAIL"}  {label:<56} -> {got!r}')


print('=== tags the front-end sends today (grepped from the HTML) ===')
# contact.html sends form.product.value; index.html appends ' (waitlist)'.
check('SHIFTLOG (contact form)',            _lead_type_for('SHIFTLOG'), 'question')
check('General (contact form default)',     _lead_type_for('General'), 'question')
check('PROPERTY_SUITE (for-landlords)',     _lead_type_for('PROPERTY_SUITE'), 'question')
check('MARKUPR (waitlist)',                 _lead_type_for('MARKUPR (waitlist)'), 'waitlist')
check('OPSIQ (waitlist)',                   _lead_type_for('OPSIQ (waitlist)'), 'waitlist')
check('PROPERTY_SUITE (calculator lead)',   _lead_type_for('PROPERTY_SUITE (calculator lead)'), 'calculator')
check('MANUFACTURING_SUITE (calculator lead)', _lead_type_for('MANUFACTURING_SUITE (calculator lead)'), 'calculator')
check('PROPERTY_LEAD_MAGNET (Inspection Checklist)',
      _lead_type_for('PROPERTY_LEAD_MAGNET (Inspection Checklist)'), 'lead_magnet')
check('MANUFACTURING_LEAD_MAGNET (Shift Handoff)',
      _lead_type_for('MANUFACTURING_LEAD_MAGNET (Shift Handoff)'), 'lead_magnet')
check('MANUFACTURING_LEAD_MAGNET (NCR-CAPA Log)',
      _lead_type_for('MANUFACTURING_LEAD_MAGNET (NCR-CAPA Log)'), 'lead_magnet')
check('AFFILIATE_PROGRAM_SIGNUP',           _lead_type_for('AFFILIATE_PROGRAM_SIGNUP'), 'affiliate')
check('STOREFRONT (email capture) [retired]',
      _lead_type_for('STOREFRONT (email capture)'), 'email_capture')
check('PROPERTY (legacy row in prod DB)',   _lead_type_for('PROPERTY'), 'question')

print()
print('=== degenerate input ===')
check('empty string',                       _lead_type_for(''), 'question')
check('None',                               _lead_type_for(None), 'question')
check('lowercase marker',                   _lead_type_for('opsiq (WAITLIST)'), 'waitlist')

print()
print('=== vertical agrees with the HubSpot list, always ===')
tags = ['SHIFTLOG', 'General', 'PROPERTY_SUITE', 'MARKUPR (waitlist)',
        'OPSIQ (waitlist)', 'PROPERTY_SUITE (calculator lead)',
        'MANUFACTURING_SUITE (calculator lead)',
        'PROPERTY_LEAD_MAGNET (Inspection Checklist)',
        'MANUFACTURING_LEAD_MAGNET (Shift Handoff)',
        'AFFILIATE_PROGRAM_SIGNUP', 'STOREFRONT (email capture)', 'PROPERTY',
        '', None] + sorted(PRICE_MAP)
expect_list = {'manufacturing': HUBSPOT_LIST_MANUFACTURING,
               'property': HUBSPOT_LIST_PROPERTY, None: None}
for t in tags:
    v = _lead_vertical_for(t)
    hs = _hubspot_list_for_product(t)
    ok = expect_list[v] == hs
    if not ok:
        fails.append(f'vertical/HubSpot disagree for {t!r}: {v!r} vs list {hs!r}')
    print(f'  {"ok " if ok else "FAIL"}  {str(t):<46} vertical={str(v):<14} hubspot={hs}')

print()
print('=== every tag classifies, and the type is always a known value ===')
known = {'question', 'waitlist', 'calculator', 'lead_magnet', 'affiliate', 'email_capture'}
for t in tags:
    lt = _lead_type_for(t)
    if lt not in known:
        fails.append(f'unknown lead_type {lt!r} for {t!r}')

print()
print('=== PRICE_MAP gate: which tags set a `product` property ===')
for t in tags:
    if t in PRICE_MAP:
        print(f'  sets product: {t}')
for t in ['PROPERTY_SUITE', 'MANUFACTURING_SUITE', 'MARKUPR (waitlist)', 'General']:
    if t in PRICE_MAP:
        fails.append(f'{t!r} unexpectedly in PRICE_MAP')
    else:
        print(f'  correctly withheld: {t}')

print()
if fails:
    print('FAILURES:')
    for f in fails:
        print('  -', f)
    sys.exit(1)
print('all checks passed')
