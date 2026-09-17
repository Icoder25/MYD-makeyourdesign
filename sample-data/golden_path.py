"""The demo, as an executable script.

Run this to rehearse the exact sequence shown in the demo video against a live
backend. If it prints PASS at the end, the demo works. If it prints FAIL, the
demo is broken and the video should not be recorded yet.

    python sample-data/golden_path.py

Requires the backend running:

    uvicorn backend.main:app --port 8000
"""

import sys
import urllib.error
import urllib.request
import json

BASE = "http://localhost:8000"

BRIEF = {
    "room_width_ft": 6,
    "room_length_ft": 8,
    "budget": 250000,
    "door": {"wall": "south", "offset_in": 6, "width_in": 30, "swing": "inward"},
    "electrical_available": True,
    "required_categories": ["vanity", "basin", "faucet", "toilet", "shower"],
    "preferred_styles": ["modern", "minimalist"],
    "preferences": {
        "preferred_styles": ["modern", "minimalist"],
        "smart_feature_preference": "prefer",
        "storage_preference": "neutral",
    },
    "weights": {
        "spatial": 1, "budget": 1, "preference": 1,
        "water_efficiency": 4, "style": 1, "smart_feature": 4,
    },
    "usage": {
        "household_size": 3,
        "flushes_per_person_per_day": 4,
        "shower_minutes_per_person_per_day": 4.8,
        "faucet_minutes_per_person_per_day": 2,
    },
}

failures: list[str] = []


def call(path: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(
        f"{BASE}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST" if data else "GET",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read())


def check(label: str, condition: bool, detail: str = "") -> None:
    print(f"  {'PASS' if condition else 'FAIL'}  {label}{(' — ' + detail) if detail else ''}")
    if not condition:
        failures.append(label)


def money(value: float) -> str:
    return f"Rs {value:,.0f}"


def main() -> int:
    print("\nKOHLER AI BathPlan — golden path rehearsal")
    print("=" * 64)

    try:
        health = call("/api/v1/health")
    except urllib.error.URLError:
        print("\nBackend is not reachable at " + BASE)
        print("Start it first:  uvicorn backend.main:app --port 8000\n")
        return 2

    print("\nSTEP 1 — Service is up")
    check("catalog loaded", health["catalog_loaded"], f"{health['catalog_size']} products")
    check("deterministic planner available", health["deterministic_planner_available"])
    print(f"        vision: {'on' if health['vision_available'] else 'off (fallback)'}"
          f" | language layer: {'on' if health['llm_available'] else 'off (fallback)'}")

    print("\nSTEP 2 — Plan a 6x8 ft bathroom with a Rs 2,50,000 budget")
    plan = call("/api/v1/plan", BRIEF)
    project = plan["project_id"]
    check("plan returned options", plan["status"] == "ok", f"{len(plan['candidates'])} options")
    check(
        "search was real",
        plan["meta"]["configurations_evaluated"] > 100,
        f"{plan['meta']['configurations_evaluated']:,} configurations evaluated",
    )
    check("no figure attributed to the LLM", "llm" not in plan["meta"]["computed_by"])

    for candidate in plan["candidates"]:
        print(f"        {candidate['label']:24} {money(candidate['total_price']):>14}"
              f"   {money(candidate['remaining_budget'])} left")
    check("every option is within budget",
          all(c["total_price"] <= 250000 for c in plan["candidates"]))
    check("options are genuinely different",
          len({tuple(p["id"] for p in c["products"]) for c in plan["candidates"]})
          == len(plan["candidates"]))

    print("\nSTEP 3 — The layout is solved, not asserted")
    top = plan["candidates"][0]
    layout = top["layout"]
    check("fixtures placed with clearances", len(layout["placed"]) > 0,
          f"{len(layout['placed'])} floor-standing fixtures")
    check("nothing failed to place", layout["unplaced"] == [])
    check("room stays navigable", layout["circulation_ok"])
    for item in layout["placed"]:
        print(f"        {item['category']:14} {item['wall']:6} "
              f"{item['footprint']['width_in']:.0f}x{item['footprint']['depth_in']:.0f} in")

    print("\nSTEP 4 — Water impact is calculated and auditable")
    water = top["water_impact"]
    check("water estimate computed", water["status"] == "calculated")
    if water["status"] == "calculated":
        print(f"        {water['configuration_annual_litres']:,.0f} L/year vs baseline "
              f"{water['baseline_annual_litres']:,.0f} L/year "
              f"({water['percent_saved']:.0f}% saving)")
        check("every figure shows its formula",
              all(f["formula"] for f in water["fixtures"] if f["status"] == "calculated"))
        check("assumptions are stated", len(water["assumptions"]) >= 4)

    request = "Add a smart shower and a smart toilet and a bathtub, keep my budget"
    print(f"\nSTEP 5 — '{request}'")
    modified = call(f"/api/v1/plan/{project}/modify", {"message": request})
    print(f"        understood as: {modified['understood_as']}")
    print(f"        interpreted by: {modified['interpretation_source']}")
    for change in modified["applied_changes"]:
        print(f"        * {change}")

    after = modified["plan"]
    if after["status"] == "no_fully_compliant_configuration":
        print("\nSTEP 6 — Conflict detected. The system refuses to fake it.")
        conflict = after["conflict"]
        check("conflict is explained", len(conflict["violated_constraints"]) > 0)
        check("alternatives are offered", len(conflict["possible_relaxations"]) > 0)
        for violation in conflict["violated_constraints"][:3]:
            print(f"        [{violation['constraint']}] {violation['example_reasons'][0][:88]}")
        print("        Options offered to the user:")
        for suggestion in conflict["possible_relaxations"][:4]:
            print(f"        -> {suggestion['description'][:88]}")

        print("\nSTEP 7 — The user chooses. The plan is recomputed from scratch.")
        blocking = {
            violation["constraint"]
            for violation in conflict["violated_constraints"]
            if violation["status"] == "fail"
        }

        # Raising the budget does not make the room bigger. When the blocking
        # constraint is physical, money is not the lever — and the system says so
        # rather than quietly taking the money and failing again.
        if blocking & {"layout_fit", "circulation"}:
            print("        Note: the blocking constraint is physical, not financial.")
            print("        More budget would not change this answer.")
            print("        User chooses: drop the bathtub, keep both smart fixtures.")
            choice = {"relaxation": "drop_category", "category": "bathtub"}
        else:
            print(f"        User chooses: raise the budget to {money(400000)}.")
            choice = {"relaxation": "increase_budget", "budget": 400000}

        resolved = call(f"/api/v1/plan/{project}/resolve", choice)
        check("recomputed successfully", resolved["status"] == "ok",
              f"{len(resolved['candidates'])} options")
        for candidate in resolved["candidates"]:
            smart = sum(len(p["smart"]["features"]) for p in candidate["products"])
            print(f"        {candidate['label']:24} {money(candidate['total_price']):>14}"
                  f"   {smart} smart features")
        check("still respects the budget",
              all(c["total_price"] <= resolved["brief"]["budget"]
                  for c in resolved["candidates"]))
        check("the priority the user protected survived",
              any(p["smart"]["features"]
                  for c in resolved["candidates"] for p in c["products"]),
              "smart fixtures kept")
    else:
        check(
            "the demo request produces a conflict",
            False,
            "it was satisfied instead — the demo no longer shows conflict resolution",
        )

    print("\n" + "=" * 64)
    if failures:
        print(f"FAIL — {len(failures)} check(s) failed:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("PASS — the golden path works end to end.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
