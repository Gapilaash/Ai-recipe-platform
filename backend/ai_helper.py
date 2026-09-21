"""
Text-based AI helpers (ingredient substitution suggestions, nutrition
estimates) using the same free Gemini API key as vision.py. Everything
here is optional -- if no GEMINI_API_KEY is set, these endpoints return a
clear message instead of failing silently, and the rest of the app works
without them.
"""
import json
import re

import gemini


def ai_available() -> bool:
    return gemini.available()


def _call_gemini(prompt: str, max_tokens: int = 1024) -> str:
    # Generous token budgets: newer Gemini models spend part of the budget "thinking",
    # and a too-small limit cuts the JSON off mid-way (which is what used to show "?" for nutrition).
    return gemini.generate([{"text": prompt}], max_tokens=max_tokens, temperature=0.3, json_mode=True)


def _strip_fences(text: str) -> str:
    return re.sub(r"^```(json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()


def suggest_substitute(ingredient: str, recipe_name: str) -> dict:
    prompt = (
        f"In the context of cooking '{recipe_name}', suggest up to 3 common, "
        f"easy-to-find substitutes for the ingredient '{ingredient}'. "
        "Respond with ONLY a JSON object like: "
        '{"substitutes": [{"name": "...", "note": "short 6-12 word note on how it changes the dish"}]}. '
        "No markdown, no extra text."
    )
    text = _strip_fences(_call_gemini(prompt, max_tokens=1024))
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"substitutes": [], "raw": text}


def _to_number(value):
    """Accepts 350, "350", "350 kcal", "12.5g" -> number, anything else -> None."""
    if isinstance(value, (int, float)):
        return round(value, 1)
    if isinstance(value, str):
        m = re.search(r"-?\d+(?:\.\d+)?", value)
        if m:
            return round(float(m.group(0)), 1)
    return None


def estimate_nutrition(recipe_name: str, ingredients: list[str], servings: int) -> dict:
    prompt = (
        f"Estimate approximate per-serving nutrition for the recipe '{recipe_name}' "
        f"(serves {servings}) made from: {', '.join(ingredients)}. "
        "Respond with ONLY a JSON object like: "
        '{"calories": 350, "protein_g": 20, "carbs_g": 30, "fat_g": 12}. '
        "These are rough estimates, that's fine. Use plain numbers only (no units, "
        "no ranges, no text) for each value. No markdown, no extra text before or after."
    )
    text = _strip_fences(_call_gemini(prompt, max_tokens=1024))
    data = None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # The model added stray text around the JSON object - pull just the {...} part out
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
            except json.JSONDecodeError:
                data = None

    result = {
        "calories": _to_number((data or {}).get("calories")),
        "protein_g": _to_number((data or {}).get("protein_g")),
        "carbs_g": _to_number((data or {}).get("carbs_g")),
        "fat_g": _to_number((data or {}).get("fat_g")),
    }
    if all(v is None for v in result.values()):
        raise RuntimeError("The AI couldn't estimate the nutrition this time. Please try again.")
    return result


def suggest_freestyle_recipe(ingredients: list[str]) -> dict:
    """When local + external recipe DBs don't have a good match, ask AI to invent one."""
    prompt = (
        f"I have these ingredients: {', '.join(ingredients)}. "
        "Suggest ONE simple original recipe using mostly these ingredients "
        "(a few common pantry staples like salt/oil/water are OK to assume). "
        "Respond with ONLY a JSON object like: "
        '{"name": "...", "cook_time": 20, "servings": 2, '
        '"ingredients": ["...", "..."], "instructions": ["step 1", "step 2"]}. '
        "No markdown, no extra text."
    )
    text = _strip_fences(_call_gemini(prompt, max_tokens=2048))
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise RuntimeError("Could not parse AI recipe suggestion")


def generate_recipe_by_name(dish_name: str) -> dict:
    """'How to Cook?' feature: given just a dish name, have AI write the full recipe."""
    prompt = (
        f"Write a complete, authentic home-cook recipe for '{dish_name}'. "
        "Respond with ONLY a JSON object like: "
        '{"name": "...", "cook_time": 30, "servings": 4, "tags": ["..."], '
        '"ingredients": ["...", "..."], "instructions": ["step 1", "step 2", "..."]}. '
        "Use simple lowercase ingredient names in the ingredients list (no quantities there - "
        "put quantities inside the instructions text instead). Give at least 4 clear instruction "
        "steps. No markdown, no extra text before or after the JSON."
    )
    text = _strip_fences(_call_gemini(prompt, max_tokens=2048))
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        raise RuntimeError("Could not parse AI recipe. Try a different dish name.")
