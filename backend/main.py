"""
"What Can I Cook" - advanced FastAPI backend.
Run with: uvicorn main:app --reload
"""
from io import BytesIO
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import ai_helper
import auth
import external_recipes
import pdf_export
import vision
import database
from database import get_conn
from recipes_data import ALL_INGREDIENTS, RECIPES

app = FastAPI(title="What Can I Cook API", docs_url="/api/docs", openapi_url="/api/openapi.json", redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


RECIPES_BY_ID = {str(r["id"]): r for r in RECIPES}


# =================================================================
# Pydantic models
# =================================================================

class AuthRequest(BaseModel):
    username: str
    password: str


class PantryAddRequest(BaseModel):
    names: list[str]
    quantity: Optional[str] = None


class PantryUpdateRequest(BaseModel):
    quantity: Optional[str] = None


class MatchRequest(BaseModel):
    ingredients: list[str]
    tags: Optional[list[str]] = None
    include_external: bool = False


class SubstituteRequest(BaseModel):
    ingredient: str
    recipe_name: str


class FreestyleRequest(BaseModel):
    ingredients: list[str]


class HowToCookRequest(BaseModel):
    dish_name: str


class CustomPdfRequest(BaseModel):
    """For exporting a recipe not in the local DB (external/freestyle) as PDF."""
    name: str
    cook_time: Optional[int] = None
    servings: Optional[int] = None
    tags: Optional[list[str]] = None
    ingredients: list[str]
    instructions: list[str]
    source_note: Optional[str] = None


# =================================================================
# Helpers
# =================================================================

def normalize(name: str) -> str:
    return name.strip().lower()


def score_recipe(recipe: dict, have: set[str]) -> dict:
    needed = set(recipe["ingredients"])
    matched = needed & have
    missing = needed - have
    match_pct = round(100 * len(matched) / len(needed)) if needed else 0
    return {
        **recipe,
        "id": str(recipe["id"]),
        "match_percent": match_pct,
        "matched_ingredients": sorted(matched),
        "missing_ingredients": sorted(missing),
    }


# =================================================================
# Auth
# =================================================================

def _set_session_cookie(request: Request, response: Response, token: str):
    is_https = request.headers.get("x-forwarded-proto", request.url.scheme) == "https"
    response.set_cookie(
        "session_token", token, httponly=True, max_age=60 * 60 * 24 * 30,
        samesite="lax", secure=is_https,
    )


@app.post("/api/auth/register")
def register(req: AuthRequest, request: Request, response: Response):
    user_id = auth.create_user(req.username, req.password)
    token = auth.create_session(user_id)
    _set_session_cookie(request, response, token)
    return {"ok": True, "username": req.username.strip().lower()}


@app.post("/api/auth/login")
def login(req: AuthRequest, request: Request, response: Response):
    user_id = auth.authenticate(req.username, req.password)
    token = auth.create_session(user_id)
    _set_session_cookie(request, response, token)
    return {"ok": True, "username": req.username.strip().lower()}


@app.post("/api/auth/logout")
def logout(response: Response):
    response.delete_cookie("session_token")
    return {"ok": True}


@app.get("/api/auth/me")
def me(user=Depends(auth.get_current_user_optional)):
    return {"user": user}


# =================================================================
# Meta / health
# =================================================================

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "vision_enabled": vision.vision_available(),
        "ai_enabled": ai_helper.ai_available(),
        "database": database.backend_name(),
        "database_status": database.ping(),
    }


@app.get("/api/ingredients/known")
def known_ingredients():
    return {"ingredients": ALL_INGREDIENTS}


# =================================================================
# Vision / ingredient detection
# =================================================================

@app.post("/api/detect-ingredients")
async def detect_ingredients(photo: UploadFile = File(...)):
    if not vision.vision_available():
        raise HTTPException(
            status_code=503,
            detail="Vision detection needs a free GEMINI_API_KEY (see backend/.env.example), or use manual entry.",
        )
    image_bytes = await photo.read()
    try:
        ingredients = vision.detect_ingredients(image_bytes, photo.content_type or "image/jpeg")
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"detected": ingredients}


# =================================================================
# Pantry (per-user)
# =================================================================

@app.get("/api/pantry")
def get_pantry(user=Depends(auth.get_current_user)):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM pantry WHERE user_id = ? ORDER BY name",
            (user["id"],),
        ).fetchall()
        return {"pantry": [dict(r) for r in rows]}


@app.post("/api/pantry")
def add_to_pantry(req: PantryAddRequest, user=Depends(auth.get_current_user)):
    with get_conn() as conn:
        for raw in req.names:
            name = normalize(raw)
            if not name:
                continue
            conn.execute(
                """
                INSERT INTO pantry (user_id, name, quantity) VALUES (?, ?, ?)
                ON CONFLICT(user_id, name) DO UPDATE SET quantity = excluded.quantity
                """,
                (user["id"], name, req.quantity or ""),
            )
        conn.commit()
        rows = conn.execute("SELECT * FROM pantry WHERE user_id = ? ORDER BY name", (user["id"],)).fetchall()
        return {"pantry": [dict(r) for r in rows]}


@app.patch("/api/pantry/{item_id}")
def update_pantry_item(item_id: int, req: PantryUpdateRequest, user=Depends(auth.get_current_user)):
    with get_conn() as conn:
        conn.execute(
            "UPDATE pantry SET quantity = COALESCE(?, quantity) WHERE id = ? AND user_id = ?",
            (req.quantity, item_id, user["id"]),
        )
        conn.commit()
    return {"ok": True}


@app.delete("/api/pantry/{item_id}")
def remove_from_pantry(item_id: int, user=Depends(auth.get_current_user)):
    with get_conn() as conn:
        conn.execute("DELETE FROM pantry WHERE id = ? AND user_id = ?", (item_id, user["id"]))
        conn.commit()
    return {"ok": True}


@app.delete("/api/pantry")
def clear_pantry(user=Depends(auth.get_current_user)):
    with get_conn() as conn:
        conn.execute("DELETE FROM pantry WHERE user_id = ?", (user["id"],))
        conn.commit()
    return {"ok": True}


# =================================================================
# Recipe matching (local DB + optional free TheMealDB expansion)
# =================================================================

@app.post("/api/recipes/match")
def match_recipes(req: MatchRequest):
    have = {normalize(i) for i in req.ingredients}
    results = [score_recipe(r, have) for r in RECIPES]

    if req.tags:
        wanted_tags = {t.lower() for t in req.tags}
        results = [r for r in results if wanted_tags & set(r.get("tags", []))]

    results.sort(key=lambda r: (-r["match_percent"], len(r["missing_ingredients"])))

    external = []
    if req.include_external and have:
        # Free TheMealDB lookup by the single most distinctive ingredient the user has
        seed = sorted(have, key=len, reverse=True)[0]
        for hit in external_recipes.search_by_ingredient(seed, limit=6):
            external.append(hit)

    return {"recipes": results, "external": external}


@app.get("/api/recipes/{recipe_id}/image")
def get_recipe_image(recipe_id: str, response: Response):
    """Photo for a built-in recipe (looked up once by name and cached)."""
    recipe = RECIPES_BY_ID.get(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    thumb = external_recipes.find_image_for_name(recipe["name"])
    if thumb:
        response.headers["Cache-Control"] = "public, s-maxage=86400, stale-while-revalidate=604800"
    return {"thumbnail": thumb}


@app.get("/api/recipes/{recipe_id}")
def get_recipe(recipe_id: str, user=Depends(auth.get_current_user_optional)):
    recipe = RECIPES_BY_ID.get(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    have = set()
    if user:
        with get_conn() as conn:
            have = {row["name"] for row in conn.execute(
                "SELECT name FROM pantry WHERE user_id = ?", (user["id"],)
            ).fetchall()}
    return score_recipe(recipe, have)


@app.get("/api/recipes")
def list_recipes():
    return {"recipes": RECIPES}


@app.get("/api/recipes/external/{external_id}")
def get_external_recipe(external_id: str):
    recipe = external_recipes.get_full_recipe(external_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found on TheMealDB")
    return recipe


# =================================================================
# AI extras: substitutions, nutrition, freestyle recipe generation
# =================================================================

@app.post("/api/ai/substitute")
def substitute(req: SubstituteRequest):
    if not ai_helper.ai_available():
        raise HTTPException(503, "AI substitutions need a free GEMINI_API_KEY (see backend/.env.example).")
    try:
        return ai_helper.suggest_substitute(req.ingredient, req.recipe_name)
    except RuntimeError as e:
        raise HTTPException(502, str(e))


@app.get("/api/recipes/{recipe_id}/nutrition")
def nutrition(recipe_id: str):
    recipe = RECIPES_BY_ID.get(recipe_id)
    if not recipe:
        raise HTTPException(404, "Recipe not found")

    with get_conn() as conn:
        cached = conn.execute("SELECT * FROM nutrition_cache WHERE recipe_id = ?", (recipe_id,)).fetchone()
        if cached:
            row = dict(cached)
            if any(row.get(k) is not None for k in ("calories", "protein_g", "carbs_g", "fat_g")):
                return row
            # An earlier failed estimate got cached as all-empty ("?") - throw it away and retry
            conn.execute("DELETE FROM nutrition_cache WHERE recipe_id = ?", (recipe_id,))
            conn.commit()

    if not ai_helper.ai_available():
        raise HTTPException(503, "Nutrition estimates need a free GEMINI_API_KEY (see backend/.env.example).")

    try:
        data = ai_helper.estimate_nutrition(recipe["name"], recipe["ingredients"], recipe["servings"])
    except RuntimeError as e:
        raise HTTPException(502, str(e))

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO nutrition_cache (recipe_id, calories, protein_g, carbs_g, fat_g)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (recipe_id) DO UPDATE SET
                calories = excluded.calories, protein_g = excluded.protein_g,
                carbs_g = excluded.carbs_g, fat_g = excluded.fat_g
            """,
            (recipe_id, data.get("calories"), data.get("protein_g"), data.get("carbs_g"), data.get("fat_g")),
        )
        conn.commit()
    return {"recipe_id": recipe_id, **data}


@app.post("/api/ai/freestyle-recipe")
def freestyle_recipe(req: FreestyleRequest):
    if not ai_helper.ai_available():
        raise HTTPException(503, "This needs a free GEMINI_API_KEY (see backend/.env.example).")
    try:
        return ai_helper.suggest_freestyle_recipe(req.ingredients)
    except RuntimeError as e:
        raise HTTPException(502, str(e))


# =================================================================
# "How to Cook?" - search by dish name (local DB + free TheMealDB + AI fallback)
# =================================================================

@app.get("/api/how-to-cook/search")
def how_to_cook_search(q: str):
    """Quick name search across the local DB and TheMealDB, for the 'How to Cook?' box."""
    q_lower = q.strip().lower()
    local_matches = [
        {**r, "id": str(r["id"]), "source": "local"}
        for r in RECIPES if q_lower in r["name"].lower()
    ][:5]
    external_matches = external_recipes.search_by_name(q, limit=5)
    return {"local": local_matches, "external": external_matches}


@app.post("/api/how-to-cook/ai")
def how_to_cook_ai(req: HowToCookRequest):
    """When no local/TheMealDB match fits, have AI write the full recipe from just a dish name."""
    if not ai_helper.ai_available():
        raise HTTPException(503, "This needs a free GEMINI_API_KEY (see backend/.env.example).")
    try:
        return ai_helper.generate_recipe_by_name(req.dish_name)
    except RuntimeError as e:
        raise HTTPException(502, str(e))


# =================================================================
# Home page imagery (hero + photo grid)
# =================================================================

@app.get("/api/home/featured")
def home_featured(response: Response, count: int = 30):
    meals = external_recipes.featured_meals(max(1, min(count, 60)))
    if meals:
        response.headers["Cache-Control"] = "public, s-maxage=600, stale-while-revalidate=3600"
    return {"hero": meals[0] if meals else None, "meals": meals}


# =================================================================
# Explore: browse by category / world cuisine (free TheMealDB, no key needed)
# =================================================================

@app.get("/api/explore/categories")
def explore_categories(response: Response):
    categories = external_recipes.list_categories()
    if categories:
        response.headers["Cache-Control"] = "public, s-maxage=3600, stale-while-revalidate=86400"
    return {"categories": categories}


@app.get("/api/explore/areas")
def explore_areas():
    return {"areas": external_recipes.list_areas()}


@app.get("/api/explore/by-category/{category}")
def explore_by_category(category: str):
    return {"recipes": external_recipes.filter_by_category(category)}


@app.get("/api/explore/by-area/{area}")
def explore_by_area(area: str):
    return {"recipes": external_recipes.filter_by_area(area)}


# =================================================================
# Cooking / shopping list
# =================================================================

@app.post("/api/recipes/{recipe_id}/cook")
def cook_recipe(recipe_id: str, user=Depends(auth.get_current_user)):
    recipe = RECIPES_BY_ID.get(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO cook_history (user_id, recipe_id, recipe_name) VALUES (?, ?, ?)",
            (user["id"], recipe_id, recipe["name"]),
        )
        for ing in recipe["ingredients"]:
            conn.execute("DELETE FROM pantry WHERE user_id = ? AND name = ?", (user["id"], ing))
        conn.commit()
    return {"ok": True, "message": f"Marked '{recipe['name']}' as cooked."}


@app.get("/api/recipes/{recipe_id}/shopping-list")
def shopping_list(recipe_id: str, user=Depends(auth.get_current_user)):
    recipe = RECIPES_BY_ID.get(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    with get_conn() as conn:
        have = {row["name"] for row in conn.execute(
            "SELECT name FROM pantry WHERE user_id = ?", (user["id"],)
        ).fetchall()}
    missing = sorted(set(recipe["ingredients"]) - have)
    return {"recipe": recipe["name"], "missing_ingredients": missing}


# =================================================================
# PDF export (built-in reportlab, no external service)
# =================================================================

def _pdf_response(pdf_bytes: bytes, filename: str) -> StreamingResponse:
    safe_name = "".join(c for c in filename if c.isalnum() or c in " _-").strip() or "recipe"
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}.pdf"'},
    )


@app.get("/api/recipes/{recipe_id}/pdf")
def recipe_pdf(recipe_id: str, user=Depends(auth.get_current_user_optional)):
    recipe = RECIPES_BY_ID.get(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    matched, missing, nutrition = None, None, None
    if user:
        with get_conn() as conn:
            have = {row["name"] for row in conn.execute(
                "SELECT name FROM pantry WHERE user_id = ?", (user["id"],)
            ).fetchall()}
            cached = conn.execute(
                "SELECT * FROM nutrition_cache WHERE recipe_id = ?", (recipe_id,)
            ).fetchone()
            if cached:
                nutrition = dict(cached)
        needed = set(recipe["ingredients"])
        matched = sorted(needed & have)
        missing = sorted(needed - have)

    pdf_bytes = pdf_export.build_recipe_pdf(recipe, matched, missing, nutrition)
    return _pdf_response(pdf_bytes, recipe["name"])


@app.post("/api/recipes/pdf/custom")
def custom_recipe_pdf(req: CustomPdfRequest):
    """Export a TheMealDB or AI-freestyle recipe (not in the local DB) as PDF."""
    recipe = {
        "name": req.name,
        "cook_time": req.cook_time or 0,
        "servings": req.servings or 0,
        "tags": req.tags or [],
        "ingredients": req.ingredients,
        "instructions": req.instructions,
    }
    pdf_bytes = pdf_export.build_recipe_pdf(recipe, None, None, None, req.source_note)
    return _pdf_response(pdf_bytes, req.name)


@app.get("/api/history")
def cook_history(user=Depends(auth.get_current_user)):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM cook_history WHERE user_id = ? ORDER BY cooked_at DESC LIMIT 50",
            (user["id"],),
        ).fetchall()
        return {"history": [dict(r) for r in rows]}


# =================================================================
# Favorites
# =================================================================

@app.post("/api/favorites/{recipe_id}")
def add_favorite(recipe_id: str, user=Depends(auth.get_current_user)):
    if recipe_id not in RECIPES_BY_ID:
        raise HTTPException(status_code=404, detail="Recipe not found")
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO favorites (user_id, recipe_id) VALUES (?, ?) ON CONFLICT DO NOTHING",
            (user["id"], recipe_id),
        )
        conn.commit()
    return {"ok": True}


@app.delete("/api/favorites/{recipe_id}")
def remove_favorite(recipe_id: str, user=Depends(auth.get_current_user)):
    with get_conn() as conn:
        conn.execute("DELETE FROM favorites WHERE user_id = ? AND recipe_id = ?", (user["id"], recipe_id))
        conn.commit()
    return {"ok": True}


@app.get("/api/favorites")
def list_favorites(user=Depends(auth.get_current_user)):
    with get_conn() as conn:
        ids = [row["recipe_id"] for row in conn.execute(
            "SELECT recipe_id FROM favorites WHERE user_id = ?", (user["id"],)
        ).fetchall()]
    return {"recipes": [RECIPES_BY_ID[i] for i in ids if i in RECIPES_BY_ID]}


# =================================================================
# Serve frontend (so the whole app is one process)
# =================================================================

# Local dev: serve ../public from this same process. On Vercel, public/ is served by the
# CDN before requests ever reach this function, so this mount is simply never hit there.
frontend_dir = Path(__file__).parent.parent / "public"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
