"""Build the two PDFs the submission requires.

    python scripts/build_pdfs.py

Produces:
    docs/prompt-documentation.pdf   — rendered from docs/prompts.md
    docs/presentation.pdf           — the 4-slide deck

The prompt PDF is rendered from the generated markdown, which is itself
generated from the running prompt module. So the chain
`backend/llm/prompts.py -> docs/prompts.md -> docs/prompt-documentation.pdf`
has no hand-edited link in it.
"""

import html
import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

INK = colors.HexColor("#17191C")
SOFT = colors.HexColor("#5B6167")
FAINT = colors.HexColor("#8B9198")
ACCENT = colors.HexColor("#1C4F6B")
ACCENT_SOFT = colors.HexColor("#EAF1F5")
LINE = colors.HexColor("#E3E1DD")
WARN = colors.HexColor("#8A6216")
OK = colors.HexColor("#1F6B4A")


# ---------------------------------------------------------------------------
# Markdown -> PDF (prompt documentation)
# ---------------------------------------------------------------------------

def styles_for_doc() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontSize=19, leading=24,
                             textColor=INK, spaceAfter=10, spaceBefore=4),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontSize=14, leading=18,
                             textColor=ACCENT, spaceBefore=16, spaceAfter=6),
        "h3": ParagraphStyle("h3", parent=base["Heading3"], fontSize=11.5, leading=15,
                             textColor=INK, spaceBefore=11, spaceAfter=4),
        "body": ParagraphStyle("body", parent=base["BodyText"], fontSize=9.5, leading=14,
                               textColor=INK, alignment=TA_LEFT, spaceAfter=6),
        "quote": ParagraphStyle("quote", parent=base["BodyText"], fontSize=9.5, leading=14,
                                textColor=SOFT, leftIndent=10, borderPadding=4,
                                spaceAfter=6),
        "bullet": ParagraphStyle("bullet", parent=base["BodyText"], fontSize=9.5, leading=13.5,
                                 textColor=INK, leftIndent=12, bulletIndent=3, spaceAfter=3),
        "code": ParagraphStyle("code", parent=base["Code"], fontSize=7.6, leading=10,
                               textColor=INK, backColor=colors.HexColor("#F6F5F3"),
                               borderPadding=6, leftIndent=2),
        "cell": ParagraphStyle("cell", parent=base["BodyText"], fontSize=8, leading=11,
                               textColor=INK, spaceAfter=0),
        "cellhead": ParagraphStyle("cellhead", parent=base["BodyText"], fontSize=8, leading=11,
                                   textColor=colors.white, spaceAfter=0),
    }


def inline(text: str) -> str:
    """Convert the inline markdown this document actually uses."""
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<i>\1</i>", text)
    text = re.sub(r"`([^`]+?)`", r'<font face="Courier" size="8.5">\1</font>', text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<link href="\2" color="#1C4F6B">\1</link>', text)
    return text


def markdown_to_flowables(markdown: str, st: dict[str, ParagraphStyle]) -> list:
    flow: list = []
    lines = markdown.split("\n")
    index = 0

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if not stripped:
            index += 1
            continue

        if stripped.startswith("```"):
            index += 1
            block: list[str] = []
            while index < len(lines) and not lines[index].strip().startswith("```"):
                block.append(lines[index])
                index += 1
            index += 1
            if block:
                flow.append(Spacer(1, 3))
                flow.append(Preformatted("\n".join(block), st["code"]))
                flow.append(Spacer(1, 7))
            continue

        if stripped.startswith("|") and index + 1 < len(lines) and set(
            lines[index + 1].strip().replace("|", "").replace(" ", "")
        ) <= {"-", ":"}:
            rows: list[list[str]] = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                cells = [c.strip() for c in lines[index].strip().strip("|").split("|")]
                if not set("".join(cells).replace(" ", "")) <= {"-", ":"}:
                    rows.append(cells)
                index += 1
            if rows:
                flow.append(build_table(rows, st))
            continue

        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            key = "h1" if level == 1 else "h2" if level == 2 else "h3"
            flow.append(Paragraph(inline(stripped.lstrip("# ").strip()), st[key]))
            index += 1
            continue

        if stripped.startswith(">"):
            flow.append(Paragraph(inline(stripped.lstrip("> ").strip()), st["quote"]))
            index += 1
            continue

        if stripped in {"---", "***", "___"}:
            flow.append(Spacer(1, 4))
            flow.append(Table([[""]], colWidths=[470], style=TableStyle(
                [("LINEBELOW", (0, 0), (-1, -1), 0.6, LINE)])))
            flow.append(Spacer(1, 6))
            index += 1
            continue

        if re.match(r"^[-*] ", stripped):
            flow.append(Paragraph(inline(stripped[2:]), st["bullet"], bulletText="•"))
            index += 1
            continue

        if re.match(r"^\d+\. ", stripped):
            number = stripped.split(".", 1)[0]
            flow.append(Paragraph(inline(stripped.split(". ", 1)[1]), st["bullet"],
                                  bulletText=f"{number}."))
            index += 1
            continue

        paragraph = [stripped]
        index += 1
        while index < len(lines) and lines[index].strip() and not re.match(
            r"^(#|\||>|```|---|[-*] |\d+\. )", lines[index].strip()
        ):
            paragraph.append(lines[index].strip())
            index += 1
        flow.append(Paragraph(inline(" ".join(paragraph)), st["body"]))

    return flow


def build_table(rows: list[list[str]], st: dict[str, ParagraphStyle]) -> Table:
    columns = max(len(row) for row in rows)
    data = []
    for position, row in enumerate(rows):
        padded = row + [""] * (columns - len(row))
        style = st["cellhead"] if position == 0 else st["cell"]
        data.append([Paragraph(inline(cell), style) for cell in padded])

    width = 470 / columns
    table = Table(data, colWidths=[width] * columns, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAFAF9")]),
        ("GRID", (0, 0), (-1, -1), 0.4, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def page_furniture(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(FAINT)
    canvas.drawString(20 * mm, 12 * mm, "KOHLER AI BathPlan — Prompt Documentation")
    canvas.drawRightString(A4[0] - 20 * mm, 12 * mm, f"Page {doc.page}")
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.4)
    canvas.line(20 * mm, 15 * mm, A4[0] - 20 * mm, 15 * mm)
    canvas.restoreState()


def build_prompt_pdf() -> Path:
    source = REPO_ROOT / "docs" / "prompts.md"
    if not source.exists():
        raise SystemExit("docs/prompts.md is missing — run scripts/generate_prompt_docs.py first")

    target = REPO_ROOT / "docs" / "prompt-documentation.pdf"
    st = styles_for_doc()

    doc = BaseDocTemplate(
        str(target), pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=18 * mm, bottomMargin=20 * mm,
        title="KOHLER AI BathPlan — Prompt Documentation",
        author="KOHLER AI BathPlan",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="body")
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=page_furniture)])
    doc.build(markdown_to_flowables(source.read_text(encoding="utf-8"), st))
    return target


# ---------------------------------------------------------------------------
# 4-slide presentation
# ---------------------------------------------------------------------------

SLIDE = landscape(A4)


def slide_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "kicker": ParagraphStyle("kicker", parent=base["BodyText"], fontSize=9,
                                 textColor=ACCENT, spaceAfter=3, leading=11),
        "title": ParagraphStyle("title", parent=base["Heading1"], fontSize=26, leading=30,
                                textColor=INK, spaceAfter=4),
        "subtitle": ParagraphStyle("subtitle", parent=base["BodyText"], fontSize=12.5,
                                   leading=17, textColor=SOFT, spaceAfter=12),
        "h": ParagraphStyle("h", parent=base["Heading2"], fontSize=12, leading=15,
                            textColor=ACCENT, spaceBefore=6, spaceAfter=4),
        "body": ParagraphStyle("body", parent=base["BodyText"], fontSize=10, leading=14,
                               textColor=INK, spaceAfter=5),
        "small": ParagraphStyle("small", parent=base["BodyText"], fontSize=8.5, leading=11.5,
                                textColor=SOFT, spaceAfter=3),
        "bullet": ParagraphStyle("bullet", parent=base["BodyText"], fontSize=10, leading=14,
                                 textColor=INK, leftIndent=11, bulletIndent=2, spaceAfter=4),
        "mono": ParagraphStyle("mono", parent=base["Code"], fontSize=7.4, leading=9.6,
                               textColor=INK),
        "cell": ParagraphStyle("cell", parent=base["BodyText"], fontSize=8.6, leading=11.5,
                               textColor=INK, spaceAfter=0),
        "cellhead": ParagraphStyle("cellhead", parent=base["BodyText"], fontSize=8.6,
                                   leading=11.5, textColor=colors.white, spaceAfter=0),
        "big": ParagraphStyle("big", parent=base["BodyText"], fontSize=20, leading=23,
                              textColor=ACCENT, spaceAfter=1),
        "biglabel": ParagraphStyle("biglabel", parent=base["BodyText"], fontSize=8,
                                   leading=10, textColor=FAINT, spaceAfter=0),
    }


def slide_furniture(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFillColor(ACCENT)
    canvas.rect(0, SLIDE[1] - 4, SLIDE[0], 4, stroke=0, fill=1)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(FAINT)
    canvas.drawString(16 * mm, 9 * mm, "KOHLER AI BathPlan — KOHLER–MIT-WPU AI Research Lab, Track 1")
    canvas.drawRightString(SLIDE[0] - 16 * mm, 9 * mm, f"{doc.page} / 4")
    canvas.restoreState()


def stat_row(items: list[tuple[str, str]], st) -> Table:
    cells = [[Paragraph(value, st["big"]) for value, _ in items],
             [Paragraph(label, st["biglabel"]) for _, label in items]]
    table = Table(cells, colWidths=[(SLIDE[0] - 32 * mm) / len(items)] * len(items))
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 0),
        ("TOPPADDING", (0, 1), (-1, 1), 0),
    ]))
    return table


def two_column(left: list, right: list, ratio: tuple[float, float] = (0.5, 0.5)) -> Table:
    width = SLIDE[0] - 32 * mm
    table = Table([[left, right]], colWidths=[width * ratio[0], width * ratio[1]])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, 0), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), 10),
        ("LEFTPADDING", (1, 0), (1, 0), 10),
        ("RIGHTPADDING", (1, 0), (-1, -1), 0),
    ]))
    return table


def comparison_table(rows: list[list[str]], st) -> Table:
    data = [[Paragraph(cell, st["cellhead"]) for cell in rows[0]]]
    data += [[Paragraph(cell, st["cell"]) for cell in row] for row in rows[1:]]
    width = (SLIDE[0] - 32 * mm) / 2
    table = Table(data, colWidths=[width * 0.30, width * 0.32, width * 0.38])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAFAF9")]),
        ("GRID", (0, 0), (-1, -1), 0.4, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return table


ARCHITECTURE = """ Your brief ──▶ React frontend ──▶ FastAPI
                                    │
        ┌───────────────────────────┼──────────────────────────┐
        │                           │                          │
   ┌────▼─────┐   advisory   ┌──────▼──────────────────┐  ┌────▼──────┐
   │  VISION  │   only ────▶ │   DETERMINISTIC CORE    │  │ LLM LAYER │
   │ (Gemini) │              │                         │  │ (Gemini)  │
   │          │   cannot     │  layout solver          │  │           │
   │confidence│   reach      │  constraint engine      │  │ interprets│
   │+ unknowns│   the core   │  recommendation engine  │  │ + explains│
   └──────────┘              │  sustainability engine  │  │  NEVER    │
                             │  product catalog        │  │  decides  │
                             └───────────┬─────────────┘  └────┬──────┘
                                         │                     │
                        ┌────────────────▼─────────────────────▼───┐
                        │ options · 2D plan · water · conflicts    │
                        └──────────────────────────────────────────┘"""


def build_presentation() -> Path:
    target = REPO_ROOT / "docs" / "presentation.pdf"
    st = slide_styles()

    doc = BaseDocTemplate(
        str(target), pagesize=SLIDE,
        leftMargin=16 * mm, rightMargin=16 * mm,
        topMargin=14 * mm, bottomMargin=14 * mm,
        title="KOHLER AI BathPlan", author="KOHLER AI BathPlan",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="slide")
    doc.addPageTemplates([PageTemplate(id="slide", frames=[frame], onPage=slide_furniture)])

    flow: list = []

    # ---- SLIDE 1: Problem + Solution ----
    flow.append(Paragraph("KOHLER–MIT-WPU AI Research Lab · Track 1", st["kicker"]))
    flow.append(Paragraph("KOHLER AI BathPlan", st["title"]))
    flow.append(Paragraph(
        "The AI can imagine a bathroom. The constraint engine decides whether it survives reality.",
        st["subtitle"]))

    left = [
        Paragraph("The problem", st["h"]),
        Paragraph(
            "People planning a bathroom do not have an imagination problem. They cannot answer "
            "the question that actually matters:", st["body"]),
        Paragraph(
            "<i>“Will these products fit in my room, together, within my budget — and if not, "
            "what should I give up?”</i>", st["body"]),
        Paragraph(
            "That is a configuration decision under hard constraints, not an image-generation "
            "problem. A 72-inch vanity does not fit a 5-foot wall no matter how good the "
            "render looks.", st["body"]),
    ]
    right = [
        Paragraph("The solution", st["h"]),
        Paragraph("A deterministic planner wrapped in a conversation:", st["body"]),
        Paragraph("Fixtures placed against walls with the clear floor plumbing codes require",
                  st["bullet"], bulletText="1."),
        Paragraph("Budget, compatibility, power and installation checked — unknowns stay unknown",
                  st["bullet"], bulletText="2."),
        Paragraph("2–3 options that differ in ways you would actually choose between",
                  st["bullet"], bulletText="3."),
        Paragraph("Water impact estimated with every formula and assumption shown",
                  st["bullet"], bulletText="4."),
        Paragraph("<b>When the requirements cannot all hold, it says so — and offers the "
                  "trade-offs it actually evaluated</b>", st["bullet"], bulletText="5."),
    ]
    flow.append(two_column(left, right))
    flow.append(Spacer(1, 8))
    flow.append(stat_row([
        ("33", "curated products"),
        ("~1,460", "configurations evaluated per plan"),
        ("130", "automated tests"),
        ("0", "figures produced by an LLM"),
    ], st))
    flow.append(PageBreak())

    # ---- SLIDE 2: Architecture ----
    flow.append(Paragraph("Architecture", st["kicker"]))
    flow.append(Paragraph("The LLM is not the source of truth", st["title"]))
    flow.append(Paragraph(
        "Feasibility, dimensions, pricing and water figures are computed before any model is "
        "called. The model receives them as given facts.", st["subtitle"]))
    flow.append(Preformatted(ARCHITECTURE, st["mono"]))
    flow.append(Spacer(1, 6))
    flow.append(two_column(
        [Paragraph("Enforced structurally, not by instruction", st["h"]),
         Paragraph("Vision output is typed <font face=\"Courier\" size=\"8\">authoritative: "
                   "Literal[False]</font> and has no field for a dimension or rough-in — it "
                   "<i>cannot</i> reach the engine.", st["small"]),
         Paragraph("Intent output is sanitised against a fixed vocabulary, so an invented "
                   "category is dropped before the pipeline.", st["small"]),
         Paragraph("Every response carries <font face=\"Courier\" size=\"8\">computed_by</font>. "
                   "<b>“llm” never appears in it.</b>", st["small"])],
        [Paragraph("Works with no API key", st["h"]),
         Paragraph("The AI layers are enhancements with tested fallbacks, not load-bearing "
                   "parts. With no key configured, planning, the 2D plan, water estimation, "
                   "conflict resolution and plain-language modification all still work — the "
                   "full test suite runs in this mode.", st["small"]),
         Paragraph("A model failure degrades the wording, never the verdict.", st["small"])],
    ))
    flow.append(PageBreak())

    # ---- SLIDE 3: Innovation ----
    flow.append(Paragraph("Innovation", st["kicker"]))
    flow.append(Paragraph("The most important screen is the one that says no", st["title"]))

    flow.append(two_column(
        [Paragraph("Constraint conflict resolution", st["h"]),
         Paragraph("<b>User:</b> “Add a smart shower and a smart toilet and a bathtub, "
                   "keep my budget.”", st["body"]),
         Paragraph("<b>System:</b> over budget by ₹18,300 — <i>and</i> physically "
                   "unplaceable in 6 × 8 ft.", st["body"]),
         Paragraph("It names both, and notes that <b>more budget would not fix a spatial "
                   "problem</b>. It then offers the relaxations it actually evaluated and "
                   "lets the user choose. The plan is recomputed from scratch, not patched.",
                   st["small"]),
         Paragraph("A generative tool would have returned something plausible and let the "
                   "customer discover the problem during installation.", st["small"])],
        [Paragraph("Against a generative approach", st["h"]),
         comparison_table([
             ["", "Typical AI design tool", "BathPlan"],
             ["Spatial reasoning", "Implied by a rendering", "Solved geometry, IRC clearances"],
             ["Feasibility", "Asserted", "Computed; failing check named"],
             ["Unknowns", "Filled in plausibly", "Stay unknown, surfaced"],
             ["Impossible ask", "Something close, presented as the answer",
              "Refused, explained, alternatives"],
             ["Water savings", "A percentage", "Formula + baseline + assumptions"],
             ["LLM role", "Decides", "Interprets and explains"],
         ], st)],
        ratio=(0.42, 0.58),
    ))
    flow.append(Spacer(1, 6))
    flow.append(Paragraph(
        "<b>Confidence-aware by construction.</b> A constraint report has three states, not two: "
        "<i>feasible</i>, <i>feasible pending verification</i>, and <i>infeasible</i>. An "
        "unmeasured rough-in is not the same as a mismatched one — conflating them either blocks "
        "every real plan or fakes certainty. Pending options are offered, ranked strictly below "
        "verified ones, and carry their outstanding checks with them.", st["small"]))
    flow.append(PageBreak())

    # ---- SLIDE 4: KOHLER value + roadmap ----
    flow.append(Paragraph("Value and roadmap", st["kicker"]))
    flow.append(Paragraph("A decision layer upstream of the design consultation", st["title"]))

    flow.append(two_column(
        [Paragraph("Why this matters to KOHLER", st["h"]),
         Paragraph("KOHLER already offers a human bathroom design service. BathPlan does not "
                   "compete with it — it sits in front of it, turning an undecided browser into "
                   "a customer arriving with a feasible, costed, explained configuration.",
                   st["small"]),
         Paragraph("Specification errors surface before purchase rather than at installation.",
                   st["bullet"], bulletText="•"),
         Paragraph("Smart and water-efficient products are recommended on evidence the customer "
                   "can audit, not on marketing adjectives.", st["bullet"], bulletText="•"),
         Paragraph("Every plan produces a verification list — a natural handoff to a KOHLER "
                   "consultant or installer.", st["bullet"], bulletText="•"),
         Paragraph("The catalog is designed to be swapped for an authorised live feed with no "
                   "engine change.", st["bullet"], bulletText="•")],
        [Paragraph("What we would build next", st["h"]),
         Paragraph("Authorised catalog integration — replace illustrative data with a live feed; "
                   "the schema already separates verified from illustrative fields.",
                   st["bullet"], bulletText="1."),
         Paragraph("Regional code packs — swap IRC clearances for Indian standards. The rules "
                   "are already isolated in one module.", st["bullet"], bulletText="2."),
         Paragraph("Guided rough-in capture — convert the commonest verification requirement "
                   "into a verified fact.", st["bullet"], bulletText="3."),
         Paragraph("Designer handoff package — configuration, plan and open verifications, "
                   "exported to a consultant.", st["bullet"], bulletText="4."),
         Paragraph("Konnect-informed water tracking — replace assumed usage with measured usage.",
                   st["bullet"], bulletText="5.")],
    ))
    flow.append(Spacer(1, 10))
    flow.append(KeepTogether(Table(
        [[Paragraph(
            "<b>Stated plainly:</b> prices in this prototype are illustrative and are not KOHLER "
            "pricing. Clearances are US residential-code figures used as planning minimums, and "
            "usage benchmarks are US-derived. A photograph establishes nothing measurable. This "
            "is a planning aid, not an engineering drawing — final dimensions, plumbing, "
            "electrical and local-code requirements must be verified by a qualified professional.",
            st["small"])]],
        colWidths=[SLIDE[0] - 32 * mm],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), ACCENT_SOFT),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))))

    doc.build(flow)
    return target


def main() -> int:
    prompts = build_prompt_pdf()
    print(f"Wrote {prompts.relative_to(REPO_ROOT)} ({prompts.stat().st_size:,} bytes)")
    deck = build_presentation()
    print(f"Wrote {deck.relative_to(REPO_ROOT)} ({deck.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
