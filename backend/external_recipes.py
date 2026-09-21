"""
Optional integration with TheMealDB's free public API (www.themealdb.com).
It offers a shared test key "1" that requires NO signup and NO payment for
reasonable personal use - that's what we use here. If the request fails for
any reason (offline, rate limited, etc.) callers should treat it as "no
extra results" rather than an error, since this is purely a bonus source
on top of the local recipe database.
"""
import requests

BASE = "https://www.themealdb.com/api/json/v1/1"


def search_by_ingredient(ingredient: str, limit: int = 6) -> list[dict]:
    """Free lookup: recipes containing a given main ingredient."""
    try:
        resp = requests.get(f"{BASE}/filter.php", params={"i": ingredient}, timeout=8)
        resp.raise_for_status()
        meals = resp.json().get("meals") or []
    except Exception:
        return []
    return [
        {
            "external_id": m["idMeal"],
            "name": m["strMeal"],
            "thumbnail": m["strMealThumb"],
            "source": "TheMealDB",
        }
        for m in meals[:limit]
    ]


def list_categories() -> list[dict]:
    """Free: all recipe categories (Chicken, Dessert, Seafood, ...) with thumbnails."""
    try:
        resp = requests.get(f"{BASE}/categories.php", timeout=8)
        resp.raise_for_status()
        cats = resp.json().get("categories") or []
    except Exception:
        return []
    return [
        {"name": c["strCategory"], "thumbnail": c["strCategoryThumb"], "description": c.get("strCategoryDescription", "")[:180]}
        for c in cats
    ]


def list_areas() -> list[str]:
    """Free: all world cuisines/areas (Indian, Chinese, Italian, ...)."""
    try:
        resp = requests.get(f"{BASE}/list.php", params={"a": "list"}, timeout=8)
        resp.raise_for_status()
        areas = resp.json().get("meals") or []
    except Exception:
        return []
    return sorted(a["strArea"] for a in areas if a.get("strArea"))


def filter_by_category(category: str, limit: int = 24) -> list[dict]:
    """Free: recipes within one category."""
    try:
        resp = requests.get(f"{BASE}/filter.php", params={"c": category}, timeout=8)
        resp.raise_for_status()
        meals = resp.json().get("meals") or []
    except Exception:
        return []
    return [
        {"external_id": m["idMeal"], "name": m["strMeal"], "thumbnail": m["strMealThumb"], "source": "TheMealDB"}
        for m in meals[:limit]
    ]


def filter_by_area(area: str, limit: int = 24) -> list[dict]:
    """Free: recipes from one world cuisine/area."""
    try:
        resp = requests.get(f"{BASE}/filter.php", params={"a": area}, timeout=8)
        resp.raise_for_status()
        meals = resp.json().get("meals") or []
    except Exception:
        return []
    return [
        {"external_id": m["idMeal"], "name": m["strMeal"], "thumbnail": m["strMealThumb"], "source": "TheMealDB"}
        for m in meals[:limit]
    ]


def search_by_name(name: str, limit: int = 8) -> list[dict]:
    """Free: search recipes by (partial) dish name."""
    try:
        resp = requests.get(f"{BASE}/search.php", params={"s": name}, timeout=8)
        resp.raise_for_status()
        meals = resp.json().get("meals") or []
    except Exception:
        return []
    return [
        {"external_id": m["idMeal"], "name": m["strMeal"], "thumbnail": m["strMealThumb"], "source": "TheMealDB"}
        for m in meals[:limit]
    ]


def get_full_recipe(external_id: str) -> dict | None:
    """Fetch full details (ingredients + instructions) for one TheMealDB recipe."""
    try:
        resp = requests.get(f"{BASE}/lookup.php", params={"i": external_id}, timeout=8)
        resp.raise_for_status()
        meals = resp.json().get("meals") or []
    except Exception:
        return None
    if not meals:
        return None
    m = meals[0]

    ingredients = []
    for i in range(1, 21):
        name = (m.get(f"strIngredient{i}") or "").strip()
        measure = (m.get(f"strMeasure{i}") or "").strip()
        if name:
            ingredients.append({"name": name.lower(), "measure": measure})

    instructions = [
        s.strip() for s in (m.get("strInstructions") or "").split("\r\n") if s.strip()
    ] or [s.strip() for s in (m.get("strInstructions") or "").split("\n") if s.strip()]

    return {
        "external_id": m["idMeal"],
        "name": m["strMeal"],
        "thumbnail": m["strMealThumb"],
        "category": m.get("strCategory"),
        "area": m.get("strArea"),
        "ingredients": ingredients,
        "instructions": instructions,
        "source": "TheMealDB",
        "source_url": f"https://www.themealdb.com/meal/{m['idMeal']}",
    }


# ------------------------------------------------------------------
# Home-page imagery: featured meals + image lookup for local recipes
# ------------------------------------------------------------------
import random
import time
from concurrent.futures import ThreadPoolExecutor

_FEATURED_LETTERS = ["c", "p", "b", "s", "t", "m", "r", "a"]
_FEATURED_TTL = 60 * 30  # 30 min
_featured_cache: dict = {"at": 0.0, "meals": []}
_image_cache: dict[str, str | None] = {}


def _slim(m: dict) -> dict:
    return {
        "external_id": m["idMeal"],
        "name": m["strMeal"],
        "thumbnail": m["strMealThumb"],
        "category": m.get("strCategory"),
        "area": m.get("strArea"),
        "source": "TheMealDB",
    }


def _search_first_letter(letter: str) -> list[dict]:
    try:
        resp = requests.get(f"{BASE}/search.php", params={"f": letter}, timeout=8)
        resp.raise_for_status()
        return [_slim(m) for m in (resp.json().get("meals") or [])]
    except Exception:
        return []


def featured_meals(count: int = 30) -> list[dict]:
    """A shuffled pool of meals with photos for the home page (cached for 30 minutes)."""
    now = time.time()
    if not _featured_cache["meals"] or now - _featured_cache["at"] > _FEATURED_TTL:
        with ThreadPoolExecutor(max_workers=len(_FEATURED_LETTERS)) as pool:
            pools = list(pool.map(_search_first_letter, _FEATURED_LETTERS))
        meals = [m for group in pools for m in group]
        if meals:
            _featured_cache["meals"] = meals
            _featured_cache["at"] = now
    pool_ = list(_featured_cache["meals"])
    random.shuffle(pool_)
    return pool_[:count]


_STOPWORDS = {"classic", "simple", "easy", "quick", "fresh", "with", "and", "the", "veggie", "vegetable", "baked", "roasted"}


def find_image_for_name(name: str) -> str | None:
    """Best-effort photo for one of our built-in recipes, borrowed from TheMealDB by name."""
    key = name.strip().lower()
    if key in _image_cache:
        return _image_cache[key]

    words = [w for w in key.replace("-", " ").split() if w not in _STOPWORDS and len(w) > 2]
    words.sort(key=len, reverse=True)
    candidates = ([key] + words)[:3]  # keep lookups short: each one is a network call
    thumb = None
    for term in candidates:
        hits = search_by_name(term, limit=1)
        if hits:
            thumb = hits[0]["thumbnail"]
            break
    _image_cache[key] = thumb
    return thumb
