"""Constants for water-impact estimation.

Every value here is traceable to docs/verified-facts.md. Nothing in this file is
invented, and nothing is a measurement of any particular household.
"""

LITRES_PER_GALLON = 3.78541
DAYS_PER_YEAR = 365

# --- Regulatory baseline (docs/verified-facts.md section 2) -------------------
# US federal maximum flow standards (Energy Policy Act of 1992). This is the
# comparison point for every savings figure the product reports. A percentage
# without a stated baseline is a marketing number, so the baseline travels with
# every result.
BASELINE_TOILET_GPF = 1.6
BASELINE_SHOWER_GPM = 2.5
BASELINE_FAUCET_GPM = 2.2

BASELINE_DESCRIPTION = (
    "US federal maximum flow standards (Energy Policy Act of 1992): "
    "1.6 gpf toilets, 2.5 gpm showerheads, 2.2 gpm lavatory faucets."
)

# --- Usage assumptions (docs/verified-facts.md section 3) ---------------------
# EPA water-conservation planning benchmarks. These are published planning
# figures, not observations of the user. All are adjustable at the API boundary
# and every result carries the assumption list that produced it.
DEFAULT_FLUSHES_PER_PERSON_PER_DAY = 4.0
DEFAULT_SHOWER_MINUTES_PER_PERSON_PER_DAY = 4.8
DEFAULT_FAUCET_MINUTES_PER_PERSON_PER_DAY = 2.0
DEFAULT_HOUSEHOLD_SIZE = 3

ASSUMPTION_SOURCES = {
    "flushes_per_person_per_day": (
        "EPA water-conservation planning benchmark (4 flushes/person/day). EPA's own "
        "WaterSense calculator uses 5.05; the lower figure is used here because it "
        "produces the smaller savings estimate."
    ),
    "shower_minutes_per_person_per_day": (
        "EPA water-conservation planning benchmark (4.8 shower-minutes/person/day)."
    ),
    "faucet_minutes_per_person_per_day": (
        "Planning estimate. This is the weakest of the three assumptions and is "
        "flagged as such in every result."
    ),
}

REGIONAL_LIMITATION = (
    "These are US-derived usage benchmarks. Indian household usage patterns differ, "
    "and no equivalent per-fixture benchmark was verified for this project. Treat the "
    "usage assumptions as adjustable planning inputs, not as a description of this household."
)

DISCLAIMER = (
    "Estimated from published product flow rates and stated usage assumptions. "
    "This is a calculation, not a measurement: actual household water use depends on "
    "occupancy, habits, water pressure and installation, and is not guaranteed."
)

WATER_FIXTURE_CATEGORIES = frozenset({"toilet", "smart_toilet", "faucet", "shower", "smart_shower"})
