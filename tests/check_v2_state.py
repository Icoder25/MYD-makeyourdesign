import json
import urllib.request

# Fetch V2 state from the state endpoint
req = urllib.request.Request("http://127.0.0.1:8000/api/v1/plan/0e05de4ec3c8/state")
with urllib.request.urlopen(req) as resp:
    state = json.loads(resp.read().decode("utf-8"))

print(f"Active Version: {state['version_id']}")
print(f"Ledger keys: {list(state['ledger'].keys())}")
print(f"Ledger space status: {state['ledger']['space']['status']}")
print(f"Ledger budget status: {state['ledger']['budget']['status']}")
print(f"Ledger compatibility status: {state['ledger']['compatibility']['status']}")
print(f"Ledger installation status: {state['ledger']['installation']['status']}")
print(f"Ledger style status: {state['ledger']['style']['status']}")
print(f"Ledger water status: {state['ledger']['water']['status']}")
print(f"Ledger verification status: {state['ledger']['verification']['status']}")
print(f"Door swing: {state['layout']['door']['swing']}")
print("Products:")
for p in state["selected_products"]:
    dim = p.get("dimensions_in", {})
    print(f"  - {p['category']}: {p['name']} (width: {dim.get('width_in', 'N/A')})")
