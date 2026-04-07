# Comprehensive Test Suite for Strata CRM
# Run: python scripts/test_all.py
# Requires: CRM server running (locally or on DigitalOcean)
#
# Set environment variables before running:
#   TEST_BASE_URL  — server URL (default: http://localhost:5000)
#   TEST_USERNAME  — login username (required)
#   TEST_PASSWORD  — login password (required)
import requests
import json
import sys
import os

BASE = os.environ.get("TEST_BASE_URL", "http://localhost:5000")
USERNAME = os.environ.get("TEST_USERNAME")
PASSWORD = os.environ.get("TEST_PASSWORD")

if not USERNAME or not PASSWORD:
    print("ERROR: Set TEST_USERNAME and TEST_PASSWORD environment variables.")
    print("  Example: TEST_USERNAME=myuser TEST_PASSWORD=mypass python scripts/test_all.py")
    sys.exit(1)

s = requests.Session()
passed = 0
failed = 0
errors = []

def test(name, condition):
    global passed, failed, errors
    if condition:
        passed += 1
    else:
        failed += 1
        errors.append(name)
        print(f"  FAIL: {name}")

# Login
print(f"Testing Strata CRM at {BASE}...")
print("="*50)
try:
    r = s.post(f"{BASE}/api/auth/login", json={"username": USERNAME, "password": PASSWORD})
    test("Login", r.status_code == 200)
except:
    print(f"ERROR: Cannot connect to server at {BASE}.")
    sys.exit(1)

# Static Files
print("\n--- Static Files ---")
for path in ["/","/css/styles.css","/js/utils.js","/js/api.js","/js/app.js","/js/home.js",
             "/js/sections.js","/js/contacts.js","/js/pipeline.js","/js/map.js",
             "/js/tools.js","/js/documents.js","/js/activity.js","/js/assistant.js","/js/deal.js"]:
    r = s.get(f"{BASE}{path}")
    test(f"{path} loads ({r.status_code})", r.status_code == 200)

# API Endpoints
print("\n--- API Endpoints ---")
for ep in ["/api/auth/me","/api/stats","/api/dashboard","/api/lookups",
           "/api/sections?page=1&per_page=5","/api/sections/parishes",
           "/api/owners?page=1&per_page=5","/api/deals",
           "/api/search?q=smith","/api/assistant/suggestions",
           "/api/map/markers?state=LA&limit=100"]:
    r = s.get(f"{BASE}{ep}")
    test(f"GET {ep}", r.status_code == 200)

# Contact Detail
print("\n--- Contact Detail ---")
r = s.get(f"{BASE}/api/owners?page=1&per_page=1")
oid = r.json()['owners'][0]['owner_id']
r = s.get(f"{BASE}/api/owners/{oid}")
d = r.json()
for field in ['date_of_birth','has_bankruptcy','has_debt','has_lien','has_judgment',
              'has_evictions','has_foreclosures','relatives_json','associated_contacts',
              'contact_notes','do_not_contact','reserved_for_user_id',
              'linkedin_url','facebook_url']:
    test(f"Contact has {field}", field in d)

# Deal Detail
print("\n--- Deal Detail ---")
r = s.get(f"{BASE}/api/deals/1")
test("Deal detail endpoint", r.status_code == 200)
if r.status_code == 200:
    dd = r.json()
    for field in ['stage_name','owner_name','section_name','activities','history']:
        test(f"Deal has {field}", field in dd)

# Map Markers
print("\n--- Map Markers ---")
r = s.get(f"{BASE}/api/map/markers?state=LA&limit=100")
d = r.json()
test("Map markers returns data", d.get('count', 0) > 0)
if d.get('markers'):
    m = d['markers'][0]
    test("Marker has lat/lng", m.get('latitude',0) > 0 and m.get('longitude',0) != 0)

# Search
print("\n--- Search ---")
r = s.get(f"{BASE}/api/search?q=DeSoto")
d = r.json()
test("Search returns owners", len(d.get('owners', [])) > 0)
test("Search returns sections", len(d.get('sections', [])) > 0)

# Frontend Code
print("\n--- Frontend Code ---")
r = s.get(f"{BASE}/js/contacts.js")
js = r.text
for check in ['date_of_birth','Est. Age','has_bankruptcy','Financial Flags','relatives_json',
              'do_not_contact','DO NOT CONTACT','RESERVED FOR','toggleDNC','sms:','linkedin.com']:
    test(f"contacts.js: {check}", check in js)

r = s.get(f"{BASE}/js/app.js")
test("app.js: global search", 'runGlobalSearch' in r.text)

r = s.get(f"{BASE}/js/deal.js")
test("deal.js: viewDealDetail", 'viewDealDetail' in r.text)

r = s.get(f"{BASE}/js/map.js")
test("map.js: filterMap", 'filterMap' in r.text)

r = s.get(f"{BASE}/")
html = r.text
test("HTML: global-search", 'global-search' in html)
test("HTML: page-deal-detail", 'page-deal-detail' in html)
test("HTML: map filters", 'map-state-filter' in html)
test("HTML: compact kanban", 'kanban-board compact' in html)

# Stats
print("\n--- Data Stats ---")
r = s.get(f"{BASE}/api/stats")
st = r.json()
test(f"Total contacts: {st.get('total_owners',0):,}", st.get('total_owners',0) > 800000)
test(f"Total sections: {st.get('total_sections',0):,}", st.get('total_sections',0) > 1000)

# Results
print(f"\n{'='*50}")
print(f"RESULTS: {passed} passed, {failed} failed out of {passed+failed}")
if errors:
    print(f"\nFailed tests:")
    for e in errors:
        print(f"  - {e}")
else:
    print("\nALL TESTS PASSED!")
print(f"{'='*50}")
input("\nPress Enter to exit...")
