import json
import urllib.request

brief = {
    "room_width_ft": 6.0,
    "room_length_ft": 8.0,
    "ceiling_height_ft": 8.0,
    "door": {"wall": "south", "offset_in": 6.0, "width_in": 32.0, "swing": "inward"},
    "budget": 15000.0,
    "currency": "USD",
    "preferred_styles": ["Modern"],
}

print("1. Creating V1 baseline plan...")
req = urllib.request.Request(
    "http://127.0.0.1:8000/api/v1/plan",
    data=json.dumps(brief).encode("utf-8"),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(req) as resp:
    plan_data = json.loads(resp.read().decode("utf-8"))

project_id = plan_data["project_id"]
print(f"   Project ID: {project_id}")

# Fetch baseline active V1 design state
state_req = urllib.request.Request(f"http://127.0.0.1:8000/api/v1/plan/{project_id}/state")
with urllib.request.urlopen(state_req) as resp:
    v1_data = json.loads(resp.read().decode("utf-8"))

print(f"   V1 Active Version: {v1_data.get('version_id')}")
vanity_p = next((p for p in v1_data.get("products", []) if p.get("category") == "vanity"), None)
if vanity_p:
    print(f"   V1 Vanity: {vanity_p.get('name')} ({vanity_p.get('dimensions_in', {}).get('width_in')}\")")
print(f"   V1 Total Price: ${v1_data.get('pricing_summary', {}).get('total_price')}")

print("\n2. Requesting DesignPulse Impact ('Make vanity 60 inches.')...")
impact_req = urllib.request.Request(
    f"http://127.0.0.1:8000/api/v1/plan/{project_id}/impact",
    data=json.dumps({"message": "Make vanity 60 inches."}).encode("utf-8"),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(impact_req) as resp:
    impact_data = json.loads(resp.read().decode("utf-8"))

print(f"   Spatial Status: {impact_data.get('spatial_status')}")
print(f"   Budget Status: {impact_data.get('budget_status')}")
print(f"   Price Delta: ${impact_data.get('price_delta')}")
print("   Trade-off options returned:")
for t in impact_data.get("candidate_tradeoffs", []):
    print(f"     * [{t['id']}] {t.get('title')} (Feasible: {t.get('resulting_is_feasible')})")

chosen_tradeoff = impact_data["candidate_tradeoffs"][0]["id"]
print(f"\n3. Applying trade-off '{chosen_tradeoff}' to construct V2...")
tradeoff_req = urllib.request.Request(
    f"http://127.0.0.1:8000/api/v1/plan/{project_id}/tradeoff",
    data=json.dumps({"tradeoff_id": chosen_tradeoff}).encode("utf-8"),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(tradeoff_req) as resp:
    v2_resp = json.loads(resp.read().decode("utf-8"))

v2_state = v2_resp["v2"]
diff = v2_resp["diff"]

print("\n*** VERIFICATION RESULT: V2 SUCCESSFULLY CONSTRUCTED ***")
print(f"   V2 Version ID: {v2_state.get('version_id')}")
print(f"   V2 Version Number: {v2_state.get('version_number')}")
print(f"   V2 Parent Version ID: {v2_state.get('parent_version_id')}")
print(f"   V2 Total Price: {v2_state.get('currency')} {v2_state.get('total_price')}")
print(f"   Diff Cost Delta: {diff.get('currency')} {diff.get('cost_delta')}")
print(f"   Diff Fixture Replacements: {diff.get('product_replacements')}")
print(f"   Door Swing Adapted in V2: {v2_state.get('layout', {}).get('door', {}).get('swing')}")
print("   Decision Records in V2:")
for dr in v2_state.get("decision_records", []):
    print(f"     - [{dr.get('timestamp')}] {dr.get('action')}: {dr.get('rationale')}")
