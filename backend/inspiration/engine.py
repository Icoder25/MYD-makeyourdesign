"""Inspiration Engine for KOHLER AI BathPlan.

Translates aesthetic desires ("warm minimalist", "modern luxury brass", "classic heritage")
into curated KOHLER design directions: materials, hardware finishes, color palettes, and
product families.

CRITICAL INVARIANT:
Inspiration feeds DesignState through the brief and preference profiles.
It NEVER bypasses physical clearances, budget constraints, or compatibility rules.
"""

from backend.api.schemas import BathroomBrief, InspirationStylePreset


PRESETS: list[InspirationStylePreset] = [
    InspirationStylePreset(
        id="warm_minimalist",
        title="Warm Minimalist",
        tagline="Quiet architectural restraint with natural tactility and matte accents.",
        description=(
            "Rooted in organic minimalism, pairing clean geometric forms with warm bleached oak, "
            "honed travertine stone, and understated matte black or brushed bronze hardware. "
            "Emphasis is placed on flush vanity lines, concealed tanks, and seamless glass enclosures."
        ),
        primary_materials=["Natural Teak / Oak", "Honed Travertine", "Fluted Low-Iron Glass"],
        hardware_finishes=["Matte Black", "Brushed Bronze", "Matte White"],
        palette_tones=["#F5F2EB", "#DFD7C7", "#7D7565", "#1E1C1A"],
        recommended_families=["Purist", "Components", "Veil"],
        style_keywords=["minimalist", "modern"],
        mood_imagery_keywords=["clean lines", "earthy textures", "flush joinery"],
    ),
    InspirationStylePreset(
        id="modern_luxury",
        title="Modern Luxury",
        tagline="High-contrast glamour featuring statuary marble, brushed brass, and smart technology.",
        description=(
            "An unapologetic celebration of high luxury, combining dramatic Statuario marble slabs, "
            "vibrant brushed modern brass fittings, and state-of-the-art intelligent toilets. "
            "Features sculptural freestanding focal points and ambient architectural lighting."
        ),
        primary_materials=["Statuario Marble", "Smoked Mirror Glass", "Polished Quartz"],
        hardware_finishes=["Vibrant Brushed Moderne Brass", "Titanium", "Polished Chrome"],
        palette_tones=["#FFFFFF", "#E8DFD0", "#C5A059", "#111215"],
        recommended_families=["Numi", "Artifacts", "Purist"],
        style_keywords=["luxury", "modern", "contemporary"],
        mood_imagery_keywords=["bookmatched marble", "brushed gold accents", "smart integrated bidet"],
    ),
    InspirationStylePreset(
        id="classic_heritage",
        title="Classic Heritage",
        tagline="Timeless architectural grace with cross handles, subway bevels, and polished nickel.",
        description=(
            "A respectful nod to vintage craftsmanship and Edwardian detailing. Pairs beveled ceramic tile, "
            "traditional pedestal profiles, and high-shine polished chrome or nickel fixtures with exposed mechanical elegance."
        ),
        primary_materials=["Beveled Glazed Ceramic", "Carrara Marble", "Paneled Hardwood"],
        hardware_finishes=["Polished Chrome", "Vibrant Polished Nickel", "Oil-Rubbed Bronze"],
        palette_tones=["#FAF9F6", "#C9D1D3", "#5C6A72", "#2B303A"],
        recommended_families=["Artifacts", "Memoirs", "Devonshire"],
        style_keywords=["traditional", "transitional"],
        mood_imagery_keywords=["cross handles", "subway tile", "beveled woodwork"],
    ),
    InspirationStylePreset(
        id="industrial_modern",
        title="Industrial Modern",
        tagline="Raw concrete surfaces, architectural steel, and tactile knurled matte controls.",
        description=(
            "Urban sophistication pairing poured concrete basin counters, matte black framework, "
            "and knurled valve dials. Designed around honest materials and precision engineering."
        ),
        primary_materials=["Architectural Cast Concrete", "Matte Black Steel", "Wire Mesh Glass"],
        hardware_finishes=["Matte Black", "Brushed Stainless", "Gunmetal"],
        palette_tones=["#E2E2E0", "#9E9E9C", "#4F5257", "#1A1A1C"],
        recommended_families=["Components", "Purist", "Verdera"],
        style_keywords=["modern", "minimalist"],
        mood_imagery_keywords=["knurled controls", "concrete vanity", "steel partitions"],
    ),
    InspirationStylePreset(
        id="coastal_spa",
        title="Coastal Spa Sanctuary",
        tagline="Serene retreat with river rock pebbles, rainheads, and light ash timber.",
        description=(
            "Designed around restorative hydrotherapy, deep soaking bathtubs, multi-function rainheads, "
            "and sun-washed driftwood aesthetics. Prioritizes natural light, wellness, and water conservation."
        ),
        primary_materials=["River Pebble Mosaic", "Light Ash Timber", "Frosted Glass"],
        hardware_finishes=["Brushed Nickel", "Vibrant Brushed Moderne Brass", "Polished Chrome"],
        palette_tones=["#F7F8F7", "#DCE5E1", "#8FA89B", "#425C51"],
        recommended_families=["Purist", "Veil", "Artifacts"],
        style_keywords=["contemporary", "minimalist", "transitional"],
        mood_imagery_keywords=["deep soaking tub", "rainhead shower", "pebble floor"],
    ),
]

PRESETS_BY_ID = {p.id: p for p in PRESETS}


class InspirationEngine:
    """Manages aesthetic inspiration presets and maps user design requests into brief updates."""

    def list_presets(self) -> list[InspirationStylePreset]:
        return list(PRESETS)

    def get_preset(self, preset_id: str) -> InspirationStylePreset | None:
        return PRESETS_BY_ID.get(preset_id)

    def match_preset(self, query: str) -> InspirationStylePreset:
        """Deterministically match a style query to the best preset."""
        text = query.lower()
        if any(w in text for w in ["warm", "minimal", "travertine", "wood", "earth", "teak"]):
            return PRESETS_BY_ID["warm_minimalist"]
        if any(w in text for w in ["luxury", "gold", "brass", "numi", "statuary", "expensive", "glamour"]):
            return PRESETS_BY_ID["modern_luxury"]
        if any(w in text for w in ["classic", "heritage", "traditional", "retro", "vintage", "memoir", "carrara"]):
            return PRESETS_BY_ID["classic_heritage"]
        if any(w in text for w in ["industrial", "concrete", "steel", "black", "knurled", "urban"]):
            return PRESETS_BY_ID["industrial_modern"]
        if any(w in text for w in ["spa", "coastal", "sanctuary", "wellness", "rain", "pebble"]):
            return PRESETS_BY_ID["coastal_spa"]

        # Default to warm minimalist
        return PRESETS_BY_ID["warm_minimalist"]

    def apply_preset_to_brief(
        self, brief: BathroomBrief, preset: InspirationStylePreset
    ) -> BathroomBrief:
        """Translate the selected inspiration preset into brief styles and preferences."""
        new_styles = list(dict.fromkeys([*preset.style_keywords, *brief.preferred_styles]))
        return brief.model_copy(
            update={
                "preferred_styles": new_styles,
                "preferences": brief.preferences.model_copy(
                    update={"preferred_styles": new_styles}
                ),
            }
        )


inspiration_engine = InspirationEngine()
