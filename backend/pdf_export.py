"""
Generates a printable/downloadable PDF for a single recipe: title, meta info,
ingredients (with have/missing marks), full instructions, and nutrition info
if it's already been estimated. Built with reportlab - completely free,
open-source, no external service.
"""
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

BASIL = colors.HexColor("#2F4B3C")
YOLK = colors.HexColor("#E7A72C")
INK_SOFT = colors.HexColor("#5B6B54")
TOMATO = colors.HexColor("#C1432E")
LINE = colors.HexColor("#E1DAC6")


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="RecipeTitle", fontName="Helvetica-Bold", fontSize=22,
        textColor=BASIL, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="MetaLine", fontName="Helvetica", fontSize=10.5,
        textColor=INK_SOFT, spaceAfter=14,
    ))
    styles.add(ParagraphStyle(
        name="SectionHeading", fontName="Helvetica-Bold", fontSize=13,
        textColor=BASIL, spaceBefore=16, spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="IngredientHave", fontName="Helvetica", fontSize=10.5,
        textColor=colors.HexColor("#21301F"), spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="IngredientMissing", fontName="Helvetica", fontSize=10.5,
        textColor=TOMATO, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="StepText", fontName="Helvetica", fontSize=11,
        textColor=colors.HexColor("#21301F"), leading=15, spaceAfter=10,
    ))
    styles.add(ParagraphStyle(
        name="TagText", fontName="Helvetica-Oblique", fontSize=9.5,
        textColor=INK_SOFT, spaceAfter=14,
    ))
    styles.add(ParagraphStyle(
        name="Footer", fontName="Helvetica-Oblique", fontSize=8.5,
        textColor=INK_SOFT, alignment=1,
    ))
    return styles


def build_recipe_pdf(
    recipe: dict,
    matched_ingredients: list[str] | None = None,
    missing_ingredients: list[str] | None = None,
    nutrition: dict | None = None,
    source_note: str | None = None,
) -> bytes:
    """Returns raw PDF bytes for the given recipe dict.

    recipe needs: name, cook_time, servings, tags, ingredients, instructions.
    matched/missing lists are optional -- if omitted, all ingredients are
    shown plain (used for external/freestyle recipes with no pantry context).
    """
    styles = _styles()
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        topMargin=0.7 * inch, bottomMargin=0.7 * inch,
        title=recipe["name"],
    )
    story = []

    # Title + meta
    story.append(Paragraph(recipe["name"], styles["RecipeTitle"]))
    meta = f"{recipe.get('cook_time', '?')} min &nbsp;&nbsp;•&nbsp;&nbsp; {recipe.get('servings', '?')} servings"
    story.append(Paragraph(meta, styles["MetaLine"]))

    tags = recipe.get("tags") or []
    if tags:
        story.append(Paragraph(" · ".join(t.title() for t in tags), styles["TagText"]))

    # Divider
    story.append(Table([[""]], colWidths=[6.5 * inch], rowHeights=[1],
                        style=TableStyle([("LINEBELOW", (0, 0), (-1, -1), 1, LINE)])))
    story.append(Spacer(1, 12))

    # Ingredients
    story.append(Paragraph("Ingredients", styles["SectionHeading"]))
    ingredients = recipe.get("ingredients", [])
    have = set(matched_ingredients) if matched_ingredients is not None else set(ingredients)
    for ing in ingredients:
        is_have = ing in have
        mark = "&#10003;" if is_have else "&#43;"
        style = styles["IngredientHave"] if is_have else styles["IngredientMissing"]
        label = ing.title() if is_have else f"{ing.title()} (need to buy)"
        story.append(Paragraph(f"{mark}&nbsp;&nbsp;{label}", style))

    # Nutrition (only if we have it)
    if nutrition and any(nutrition.get(k) is not None for k in ("calories", "protein_g", "carbs_g", "fat_g")):
        story.append(Paragraph("Nutrition (per serving, AI-estimated)", styles["SectionHeading"]))
        data = [
            ["Calories", "Protein", "Carbs", "Fat"],
            [
                str(nutrition.get("calories", "?")),
                f"{nutrition.get('protein_g', '?')}g",
                f"{nutrition.get('carbs_g', '?')}g",
                f"{nutrition.get('fat_g', '?')}g",
            ],
        ]
        t = Table(data, colWidths=[1.5 * inch] * 4)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1ECDE")),
            ("TEXTCOLOR", (0, 0), (-1, 0), BASIL),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, 1), "Helvetica"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, LINE),
        ]))
        story.append(t)
        story.append(Spacer(1, 6))

    # Instructions
    story.append(Paragraph("Instructions", styles["SectionHeading"]))
    for i, step in enumerate(recipe.get("instructions", []), start=1):
        story.append(Paragraph(f"<b>{i}.</b>&nbsp;&nbsp;{step}", styles["StepText"]))

    story.append(Spacer(1, 24))
    footer_text = source_note or "Generated by What Can I Cook — whatcanicook (self-hosted, free)"
    story.append(Paragraph(footer_text, styles["Footer"]))

    doc.build(story)
    return buf.getvalue()
