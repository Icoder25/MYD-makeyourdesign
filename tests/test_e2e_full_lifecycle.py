import json
import urllib.request
import urllib.error

def run_test():
    base = "http://127.0.0.1:8000/api/v1"
    
    # 1. Health check
    with urllib.request.urlopen(f"{base}/health") as r:
        health = json.loads(r.read())
        print(f"1. Health: catalog={health['catalog_size']}, vision={health['vision_available']}, llm={health['llm_available']}")
        assert health["status"] == "ok"
    
    # 2. Create Plan
    payload = {
        "room_width_ft": 6.0,
        "room_length_ft": 8.0,
        "budget": 250000,
        "currency": "INR",
        "required_categories": ["vanity", "basin", "faucet", "toilet", "shower"],
        "preferred_styles": ["modern", "minimalist"],
        "door": {"wall": "south", "offset_in": 6, "width_in": 30, "swing": "inward"}
    }
    req = urllib.request.Request(
        f"{base}/plan",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as r:
        plan = json.loads(r.read())
        pid = plan["project_id"]
        print(f"2. Plan created: project_id={pid}, candidates={len(plan['candidates'])}")
        assert len(plan["candidates"]) > 0

    # 3. Read State (V1)
    with urllib.request.urlopen(f"{base}/plan/{pid}/state") as r:
        v1_state = json.loads(r.read())
        print(f"3. V1 State read: version_id={v1_state['version_id']}, products={len(v1_state['selected_products'])}")
        assert v1_state["version_id"] == "v1"

    # 4. DesignPulse Impact Analysis
    impact_req = urllib.request.Request(
        f"{base}/plan/{pid}/impact",
        data=json.dumps({"message": "Make vanity 60 inches."}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(impact_req) as r:
        impact = json.loads(r.read())
        print(f"4. Impact analyzed: changed={impact['changed_category']}, tradeoffs={len(impact['candidate_tradeoffs'])}")
        assert len(impact["candidate_tradeoffs"]) > 0
        tradeoff = impact["candidate_tradeoffs"][0]

    # 5. Apply Trade-off -> Construct V2 (endpoint: POST /plan/{pid}/tradeoff)
    apply_req = urllib.request.Request(
        f"{base}/plan/{pid}/tradeoff",
        data=json.dumps({"tradeoff_id": tradeoff["id"], "tradeoff": tradeoff}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(apply_req) as r:
        apply_res = json.loads(r.read())
        v2 = apply_res["v2"]
        diff = apply_res["diff"]
        print(f"5. V2 Applied: version_id={v2['version_id']}, door_swing={v2['layout']['door']['swing']}")
        assert v2["version_id"] == "v2"
        assert v2["parent_version_id"] == "v1"

    # 6. Read Diff V1 vs V2
    with urllib.request.urlopen(f"{base}/plan/{pid}/diff?from_version=v1&to_version=v2") as r:
        diff_res = json.loads(r.read())
        print(f"6. Diff retrieved: from={diff_res['from_version']} -> to={diff_res['to_version']}, delta={diff_res['price_delta']}")
        assert diff_res["from_version"] == "v1" and diff_res["to_version"] == "v2"

    # 7. Sustainability / Water Impact Check
    assert "water_impact" in v2
    print(f"7. Sustainability: status={v2['water_impact']['status']}, annual_saved={v2['water_impact'].get('annual_litres_saved')} L")

    # 8. Export Packages (Client, Designer, Dealer)
    for role in ["client", "designer", "dealer"]:
        with urllib.request.urlopen(f"{base}/plan/{pid}/export?role={role}&version_id=v2") as r:
            pkg = json.loads(r.read())
            assert pkg["role"] == role
            assert pkg["version_id"] == "v2"
            print(f"8. Export {role}: ok, package_type={pkg['data'].get('package_type')}")

    # 9. HTML Printable Export Document
    with urllib.request.urlopen(f"{base}/plan/{pid}/export/document?role=dealer&version_id=v2") as r:
        html = r.read().decode("utf-8")
        assert "<!DOCTYPE html>" in html or "<html" in html
        print(f"9. HTML Export document: ok, length={len(html)} chars")

    print("\n========================================================")
    print("ALL 9 END-TO-END BACKEND VERIFICATIONS PASSED 100%!")
    print("========================================================")

if __name__ == "__main__":
    run_test()
