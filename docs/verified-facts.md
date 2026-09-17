# KOHLER AI BathPlan — Verified Facts Register

> **Purpose.** Every number this system uses in a calculation must trace to one of
> three states: **VERIFIED** (external source, cited below), **ASSUMPTION**
> (documented, user-adjustable, never presented as measurement), or
> **ILLUSTRATIVE** (prototype placeholder, never presented as a KOHLER fact).
>
> This file is the register. Code reads these constants from
> `backend/sustainability/constants.py` and `catalog/products.json`; this
> document is why those values are what they are.
>
> **Verified on:** 2026-09-18.

---

## 1. VERIFIED — Efficiency thresholds (EPA WaterSense)

These thresholds decide whether the catalog may flag a product `watersense_eligible`.
They are certification *criteria*, not claims about any specific KOHLER product.

| Fixture | WaterSense maximum | Notes |
|---|---|---|
| Toilet | **1.28 gpf** (4.85 L/flush) | Maximum flush volume permitted under the specification |
| Bathroom (lavatory) faucet | **1.5 gpm** at 60 psi | Must also deliver at least 0.8 gpm at 20 psi |
| Showerhead | **2.0 gpm** | A 20% reduction against the federal 2.5 gpm standard |

Source: [EPA WaterSense — Bathroom Faucets](https://www.epa.gov/watersense/bathroom-faucets),
[EPA WaterSense — Showerheads](https://www.epa.gov/watersense/showerheads),
[EPA WaterSense — Residential Toilets](https://www.epa.gov/watersense/residential-toilets).

**Rule for this codebase:** a catalog entry may set `watersense_eligible: true` only
when its own recorded flow/flush figure meets the threshold above. This is a
*computed eligibility flag*, and the catalog records it as such. It is **not** a
claim that KOHLER has certified that SKU. Certification status per SKU is
`verification_status: "requires_verification"` throughout.

---

## 2. VERIFIED — Regulatory baseline for savings comparison

Savings are meaningless without a stated baseline. This system compares against the
US federal maximum flow standards (Energy Policy Act of 1992), which is also the
baseline EPA itself uses when expressing WaterSense savings:

| Fixture | Federal standard baseline |
|---|---|
| Toilet | 1.6 gpf |
| Showerhead | 2.5 gpm |
| Lavatory faucet | 2.2 gpm |

Source: [EPA WaterSense — Showerheads](https://www.epa.gov/watersense/showerheads) (2.5 gpm federal standard),
[EPA WaterSense — Residential Toilets](https://www.epa.gov/watersense/residential-toilets).

**Rule:** the UI must always print the baseline next to any savings figure. A
percentage with no baseline is a marketing number, not an engineering one.

---

## 3. ASSUMPTION — Usage behaviour defaults

These are **not** measurements of the user's household. They are published
planning benchmarks, exposed in the UI as editable inputs, and every water result
must ship with the assumption list that produced it.

| Assumption | Default | Basis |
|---|---|---|
| Toilet flushes per person per day | **4.0** | EPA water-conservation planning benchmark |
| Shower minutes per person per day | **4.8** | EPA water-conservation planning benchmark |
| Faucet minutes per person per day | **2.0** | Planning estimate — weakest of the three, flagged in output |
| Household size | **3** | Prototype default; always user-set in the demo |
| Days per year | 365 | — |

Source: [EPA Water Conservation Plan Guidelines, Appendix B](https://www.epa.gov/sites/default/files/2017-03/documents/appendix-b-benchmarks-used-in-conservation-planning.pdf),
[EPA — Indoor Water Use in the United States](https://www.epa.gov/sites/default/files/2017-03/documents/ws-facthseet-indoor-water-use-in-the-us.pdf).

Note: EPA's WaterSense calculator uses 5.05 flushes/person/day rather than the
4.0 planning benchmark. We use 4.0 (the more conservative figure, producing
*smaller* claimed savings) and expose it as adjustable. Choosing the number that
makes our own result look worse is deliberate.

**Known limitation, stated in-product:** these are US-derived benchmarks. Indian
household usage patterns differ, and no equivalent per-fixture benchmark was
verified for India within this project's window. The output labels this.

---

## 4. VERIFIED — KOHLER Anthem EvoCycle claim (wording preserved)

KOHLER states the Anthem EvoCycle recirculating shower system delivers
**"up to 80% water savings"** while maintaining full flow rate.

Manufacturer-stated mechanism and assumptions, preserved rather than generalised:
when paired with a 2.5 gpm showerhead or rainhead, the system uses approximately
**2 gallons of recirculated water for every 0.5 gallons of fresh water per minute**.
KOHLER states actual savings vary with shower duration and Cycle Mode usage.

Source: [KOHLER — Anthem EvoCycle](https://www.kohler.com/en/products/showers/anthem-evocycle),
[KOHLER press release via PR Newswire](https://www.prnewswire.com/news-releases/kohler-introduces-anthem-evocycle-smart-shower-a-breakthrough-recirculating-shower-system-designed-for-sustainable-living-302685684.html),
[ASPE Pipeline coverage](https://aspe.org/pipeline/kohler-introduces-anthem-evocycle-smart-shower-designed-for-sustainable-living/).

**Rule for this codebase:** where a product carries a manufacturer claim, the
catalog stores it as a structured `manufacturer_claim` object carrying the claim
type (`up_to`), the value, the comparison baseline, and the source URL. The
sustainability engine surfaces it **verbatim and attributed** and does **not**
fold an "up to" marketing figure into a computed annual total. Computed totals use
only measured flow/flush figures. This distinction is enforced in code, not policy.

---

## 5. ILLUSTRATIVE — Pricing

**No live KOHLER pricing API was available to this project.** Every price in
`catalog/products.json` carries `price_status: "illustrative"` and exists only to
make budget arithmetic demonstrable.

Prices are set to plausible Indian-market tiers for the product class. They are
**not** quotes, **not** MRP, and **not** scraped from KOHLER. The UI labels them.
The catalog is structured so an authorised live price feed can replace the
`price` and `price_status` fields without touching any engine code.

---

## 6. ILLUSTRATIVE — Product dimensions

Where a dimension could not be verified against a public specification sheet
within the project window, the catalog records a plausible class-typical figure
with `verification_status: "illustrative"`. The constraint engine treats an
absent dimension as `verification_required` and never as a pass — so a missing
figure degrades to a verification prompt rather than a false clearance.

---

## 7. Unit convention

KOHLER US specification sheets publish gpf/gpm. Indian users think in litres.
The engine computes internally in **litres** and converts on input at
**1 US gallon = 3.78541 L**. Both units appear in output.

---

## 8. What this register deliberately does not claim

- That any specific KOHLER SKU is WaterSense-certified. Eligibility is computed
  from recorded flow figures; certification is `requires_verification`.
- That the prices are real.
- That the computed annual figures are measured household consumption.
- That US usage benchmarks describe an Indian household.
- That a photograph established any dimension, rough-in, or electrical fact.
