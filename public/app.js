// ===========================================================
// Config
// ===========================================================
const API_BASE = ""; // same-origin: backend serves this frontend too

// ===========================================================
// State
// ===========================================================
let knownIngredients = [];
let stagedIngredients = new Set();
let currentRecipes = [];
let activeTagFilters = new Set();
let currentUser = null;
let cookModeState = null; // { steps, index }
let currentTab = "home";
let recipePrevTab = "home";
let recipePrevScroll = 0;

// ===========================================================
// Theme (cream light theme by default, dark optional)
// ===========================================================
function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem("theme", theme);
  document.querySelectorAll(".theme-toggle").forEach((btn) => {
    btn.textContent = theme === "dark" ? "Light" : "Dark";
  });
}

function initTheme() {
  applyTheme(localStorage.getItem("theme") === "dark" ? "dark" : "light");
}

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") || "light";
  applyTheme(current === "dark" ? "light" : "dark");
}

document.getElementById("themeToggle").addEventListener("click", toggleTheme);
document.getElementById("themeToggleLanding").addEventListener("click", toggleTheme);
initTheme();

// ===========================================================
// Utilities
// ===========================================================
async function api(path, opts = {}) {
  const res = await fetch(API_BASE + path, {
    credentials: "include",
    headers: opts.body instanceof FormData ? {} : { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    const e = new Error(err.detail || "Request failed");
    e.status = res.status;
    throw e;
  }
  return res.json();
}

function showToast(msg) {
  const toast = document.getElementById("toast");
  toast.textContent = msg;
  toast.classList.remove("hidden");
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => toast.classList.add("hidden"), 2800);
}

function titleCase(s) {
  return String(s).replace(/\b\w/g, (c) => c.toUpperCase());
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function bgUrl(el, url) {
  el.style.backgroundImage = `url("${String(url).replace(/"/g, "%22")}")`;
  el.classList.remove("skeleton");
}

// ===========================================================
// AUTH
// ===========================================================
const authScreen = document.getElementById("authScreen");
const appShell = document.getElementById("appShell");
const authForm = document.getElementById("authForm");
const authError = document.getElementById("authError");
const authSubmitBtn = document.getElementById("authSubmitBtn");
let authMode = "login";

function setAuthMode(mode) {
  authMode = mode;
  document.querySelectorAll(".auth-tab").forEach((b) => b.classList.toggle("active", b.dataset.mode === mode));
  authSubmitBtn.textContent = mode === "login" ? "Log in" : "Create account";
  authError.textContent = "";
  const title = document.getElementById("authTitle");
  const subtitle = document.getElementById("authSubtitle");
  const switchText = document.getElementById("authSwitchText");
  const switchBtn = document.getElementById("authSwitchBtn");
  if (mode === "login") {
    title.textContent = "Welcome back";
    subtitle.textContent = "Log in to continue your cooking journey";
    switchText.textContent = "Don't have an account?";
    switchBtn.textContent = "Sign up";
  } else {
    title.textContent = "Create your account";
    subtitle.textContent = "Sign up to start cooking smarter";
    switchText.textContent = "Already have an account?";
    switchBtn.textContent = "Log in";
  }
}

document.querySelectorAll(".auth-tab").forEach((btn) => {
  btn.addEventListener("click", () => setAuthMode(btn.dataset.mode));
});

document.getElementById("authSwitchBtn").addEventListener("click", () => {
  setAuthMode(authMode === "login" ? "register" : "login");
});

document.getElementById("authPwdToggle").addEventListener("click", (e) => {
  const pwd = document.getElementById("authPassword");
  const isHidden = pwd.type === "password";
  pwd.type = isHidden ? "text" : "password";
  e.target.textContent = isHidden ? "Hide" : "Show";
});

document.getElementById("authForgot").addEventListener("click", (e) => {
  e.preventDefault();
  authError.textContent = "Passwords are stored locally on this server — ask whoever manages it to reset your account.";
});

authForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  authError.textContent = "";
  const username = document.getElementById("authUsername").value;
  const password = document.getElementById("authPassword").value;
  authSubmitBtn.disabled = true;
  try {
    const path = authMode === "login" ? "/api/auth/login" : "/api/auth/register";
    const data = await api(path, { method: "POST", body: JSON.stringify({ username, password }) });
    currentUser = data.username;
    enterApp();
  } catch (err) {
    authError.textContent = err.message;
  } finally {
    authSubmitBtn.disabled = false;
  }
});

document.getElementById("logoutBtn").addEventListener("click", async () => {
  await api("/api/auth/logout", { method: "POST" });
  currentUser = null;
  appShell.classList.add("hidden");
  authScreen.classList.remove("hidden");
  authForm.reset();
  loadAuthCollage();
});

function enterApp() {
  document.getElementById("accountUsername").textContent = currentUser;
  authScreen.classList.add("hidden");
  appShell.classList.remove("hidden");
  initApp();
}

// Food photos on the login screen
let authCollageLoaded = false;
async function loadAuthCollage() {
  if (authCollageLoaded) return;
  try {
    const { meals } = await api("/api/home/featured?count=4");
    if (!meals || !meals.length) return;
    authCollageLoaded = true;
    document.querySelectorAll("#authCollage .collage-tile").forEach((tile, i) => {
      if (meals[i]) tile.style.backgroundImage = `url("${meals[i].thumbnail}")`;
    });
  } catch { /* purely decorative */ }
}

// ===========================================================
// Tabs
// ===========================================================
document.getElementById("tabs").addEventListener("click", (e) => {
  const btn = e.target.closest(".tab");
  if (!btn) return;
  switchTab(btn.dataset.tab);
});

// Pure UI: show one panel (no data loading)
function showPanel(tab) {
  currentTab = tab;
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === tab));
  document.querySelectorAll(".panel").forEach((p) => p.classList.toggle("active", p.id === `panel-${tab}`));
}

function switchTab(tab) {
  showPanel(tab);
  if (tab === "home") loadHome();
  if (tab === "pantry") loadPantry();
  if (tab === "recipes") matchAndRenderRecipes();
  if (tab === "favorites") loadFavorites();
  if (tab === "explore") loadExplore();
  window.scrollTo({ top: 0 });
}

document.getElementById("heroScanBtn").addEventListener("click", () => switchTab("scan"));
document.getElementById("ctaScanBtn").addEventListener("click", () => switchTab("scan"));
document.getElementById("heroHowToCookBtn").addEventListener("click", () => {
  document.getElementById("howToCookBtn").click();
});

// ===========================================================
// Boot
// ===========================================================
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("sw.js").catch(() => {});
}
boot();

async function boot() {
  try {
    const { user } = await api("/api/auth/me");
    if (user) {
      currentUser = user.username;
      enterApp();
      return;
    }
  } catch {
    /* not logged in */
  }
  authScreen.classList.remove("hidden");
  loadAuthCollage();
}

async function initApp() {
  try {
    const health = await api("/api/health");
    if (!health.vision_enabled) {
      document.getElementById("visionHint").textContent =
        "Photo auto-detection needs a free Gemini API key (see backend/.env.example). You can still add ingredients manually below.";
    }
    window.__aiEnabled = health.ai_enabled;
  } catch {
    document.getElementById("visionHint").textContent = "Could not reach the backend. Is it running?";
  }

  try {
    const { ingredients } = await api("/api/ingredients/known");
    knownIngredients = ingredients;
  } catch { /* non-fatal */ }

  loadPantry();
  renderStagedChips();
  loadHome();
  loadSavedRecipesDropdown();
}

// ===========================================================
// Shared recipe card templates (photo cards)
// ===========================================================
function extCardHTML(r, sub) {
  const subline = sub ?? [r.category, r.area].filter(Boolean).join(" · ");
  return `
    <article class="rcard" data-kind="ext" data-ext-id="${esc(r.external_id)}">
      <div class="rcard-img">
        <img src="${esc(r.thumbnail)}" alt="${esc(r.name)}" loading="lazy">
      </div>
      <h3>${esc(r.name)}</h3>
      ${subline ? `<p class="rcard-sub">${esc(subline)}</p>` : ""}
      <div class="rcard-btn"><span>See Complete Recipe</span><i>&rarr;</i></div>
    </article>`;
}

function matchBadgeClass(pct) {
  if (pct >= 100) return "full";
  if (pct >= 70) return "high";
  if (pct >= 40) return "mid";
  return "low";
}

function localCardHTML(r) {
  const missing = r.missing_ingredients.slice(0, 3);
  const missingText = r.missing_ingredients.length
    ? `<p class="rcard-missing">Missing: <strong>${esc(missing.map(titleCase).join(", "))}${r.missing_ingredients.length > 3 ? "…" : ""}</strong></p>`
    : `<p class="rcard-missing all">You have everything!</p>`;
  const label = (r.tags || [])[0] ? titleCase(r.tags[0]) : "Recipe";
  return `
    <article class="rcard" data-kind="local" data-id="${esc(r.id)}">
      <div class="rcard-img" data-needs-img="1">
        <span class="noimg">${esc(label)}</span>
        <span class="match-badge ${matchBadgeClass(r.match_percent)}">${r.match_percent}%</span>
      </div>
      <h3>${esc(r.name)}</h3>
      <p class="rcard-sub">${r.cook_time} min · ${r.servings} servings</p>
      ${missingText}
      <div class="rcard-btn"><span>See Complete Recipe</span><i>&rarr;</i></div>
    </article>`;
}

// Built-in recipes have no photos of their own — borrow one lazily as each card scrolls into view.
const imageObserver = "IntersectionObserver" in window
  ? new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        imageObserver.unobserve(entry.target);
        fillLocalImage(entry.target);
      });
    }, { rootMargin: "240px" })
  : null;

function observeLocalImages(container) {
  container.querySelectorAll('.rcard-img[data-needs-img]').forEach((el) => {
    if (imageObserver) imageObserver.observe(el);
    else fillLocalImage(el);
  });
}

async function fillLocalImage(el) {
  el.removeAttribute("data-needs-img");
  const card = el.closest(".rcard");
  if (!card) return;
  try {
    const { thumbnail } = await api(`/api/recipes/${encodeURIComponent(card.dataset.id)}/image`);
    if (!thumbnail) return;
    const noimg = el.querySelector(".noimg");
    if (noimg) noimg.remove();
    el.insertAdjacentHTML("afterbegin", `<img src="${esc(thumbnail)}" alt="${esc(card.querySelector("h3").textContent)}" loading="lazy">`);
  } catch { /* leave the placeholder */ }
}

function skeletonCards(n) {
  return Array.from({ length: n }, () => `<div class="rcard-skel skeleton"></div>`).join("");
}

// One click handler for every photo card in the app
document.addEventListener("click", (e) => {
  const card = e.target.closest(".rcard[data-kind]");
  if (card) {
    if (card.dataset.kind === "local") openLocalRecipe(card.dataset.id);
    else openExternalRecipe(card.dataset.extId);
    return;
  }
  const hero = e.target.closest("#heroPhoto[data-ext-id], #heroTag[data-ext-id]");
  if (hero) openExternalRecipe(hero.dataset.extId);
});

document.getElementById("heroPhoto").addEventListener("keydown", (e) => {
  if ((e.key === "Enter" || e.key === " ") && e.target.dataset.extId) {
    e.preventDefault();
    openExternalRecipe(e.target.dataset.extId);
  }
});

// ===========================================================
// HOME — hero image, photo grid, categories, popular strip
// ===========================================================
const home = { loaded: false, loading: false, meals: [], categories: [], gridToken: 0 };

function categoryCardsHTML(categories) {
  return categories
    .map((c) => `<div class="explore-card" data-category="${esc(c.name)}">
      <img src="${esc(c.thumbnail)}" alt="${esc(c.name)}" loading="lazy">
      <div class="explore-card-label">${esc(c.name)}</div>
    </div>`)
    .join("");
}

async function loadHome() {
  if (home.loaded || home.loading) return;
  home.loading = true;
  document.getElementById("homeRecipeGrid").innerHTML = skeletonCards(8);

  const [featured, cats] = await Promise.allSettled([
    api("/api/home/featured?count=40"),
    api("/api/explore/categories"),
  ]);

  home.meals = featured.status === "fulfilled" ? featured.value.meals || [] : [];
  home.categories = cats.status === "fulfilled" ? cats.value.categories || [] : [];
  home.loading = false;
  home.loaded = home.meals.length > 0 || home.categories.length > 0;

  renderHero();
  renderHomeGrid(home.meals.slice(3, 21), "Fresh picks for you");
  renderHomePills();
  renderHomeCategories();
  renderHomeStrip();
  renderCta();
}

function renderHero() {
  const [hero, a, b] = home.meals;
  const photo = document.getElementById("heroPhoto");
  const floatA = document.getElementById("heroFloatA");
  const floatB = document.getElementById("heroFloatB");
  if (!hero) {
    // Offline / TheMealDB unreachable: keep the hero looking intentional
    [photo, floatA, floatB].forEach((el) => el.classList.remove("skeleton"));
    photo.style.background = "linear-gradient(135deg, #F5A623, #F7C567)";
    floatA.style.display = "none";
    floatB.style.display = "none";
    return;
  }
  bgUrl(photo, hero.thumbnail);
  photo.dataset.extId = hero.external_id;
  if (a) bgUrl(floatA, a.thumbnail); else floatA.style.display = "none";
  if (b) bgUrl(floatB, b.thumbnail); else floatB.style.display = "none";

  const tag = document.getElementById("heroTag");
  tag.dataset.extId = hero.external_id;
  tag.innerHTML = `<small>Today's pick</small><strong>${esc(hero.name)}</strong>`;
  tag.classList.remove("hidden");
}

function renderHomeGrid(list, note) {
  document.getElementById("homeGridNote").textContent = note || "";
  const grid = document.getElementById("homeRecipeGrid");
  if (!list || list.length === 0) {
    grid.innerHTML = `<div class="empty-state">Couldn't load recipes right now — check your internet connection.</div>`;
    return;
  }
  grid.innerHTML = list.map((r) => extCardHTML(r)).join("");
}

function renderHomePills() {
  const row = document.getElementById("homeCategoryPills");
  const names = ["All", ...home.categories.map((c) => c.name)];
  row.innerHTML = names
    .map((n, i) => `<button class="pill ${i === 0 ? "active" : ""}" data-pill="${esc(n)}">${esc(n)}</button>`)
    .join("");
}

document.getElementById("homeCategoryPills").addEventListener("click", async (e) => {
  const pill = e.target.closest(".pill");
  if (!pill) return;
  document.querySelectorAll("#homeCategoryPills .pill").forEach((p) => p.classList.toggle("active", p === pill));
  const token = ++home.gridToken;
  const name = pill.dataset.pill;
  if (name === "All") return renderHomeGrid(home.meals.slice(3, 21), "Fresh picks for you");

  document.getElementById("homeRecipeGrid").innerHTML = skeletonCards(8);
  try {
    const { recipes } = await api(`/api/explore/by-category/${encodeURIComponent(name)}`);
    if (token !== home.gridToken) return; // a newer pill was clicked
    renderHomeGrid(
      recipes.slice(0, 18).map((r) => ({ ...r, category: name })),
      `${name} recipes`
    );
  } catch {
    if (token === home.gridToken) renderHomeGrid([], "");
  }
});

function renderHomeCategories() {
  const grid = document.getElementById("homeCategoryGrid");
  grid.innerHTML = home.categories.length
    ? categoryCardsHTML(home.categories)
    : `<p class="muted">Couldn't reach TheMealDB right now — check your internet connection.</p>`;
}

function renderHomeStrip() {
  const strip = document.getElementById("homeStrip");
  const items = home.meals.slice(21, 33);
  strip.innerHTML = items.length ? items.map((r) => extCardHTML(r)).join("") : "";
  strip.previousElementSibling.style.display = items.length ? "" : "none";
}

function renderCta() {
  const pick = home.meals[33] || home.meals[4];
  const photo = document.getElementById("ctaPhoto");
  if (pick) bgUrl(photo, pick.thumbnail);
  else {
    photo.classList.remove("skeleton");
    photo.style.background = "linear-gradient(135deg, #F5A623, #F7C567)";
  }
}

document.getElementById("homeCategoryGrid").addEventListener("click", (e) => {
  const card = e.target.closest("[data-category]");
  if (!card) return;
  openCategory(card.dataset.category);
});

// ===========================================================
// SCAN TAB — photo upload + detection
// ===========================================================
const photoInput = document.getElementById("photoInput");
const photoPreview = document.getElementById("photoPreview");
const dropzoneInner = document.getElementById("dropzoneInner");
const detectBtn = document.getElementById("detectBtn");
const visionHint = document.getElementById("visionHint");

let selectedFile = null;

photoInput.addEventListener("change", () => {
  const file = photoInput.files[0];
  if (!file) return;
  selectedFile = file;
  photoPreview.src = URL.createObjectURL(file);
  photoPreview.classList.remove("hidden");
  dropzoneInner.classList.add("hidden");
  detectBtn.disabled = false;
});

// Phone photos are often 3-10 MB, but hosts like Vercel reject request bodies over ~4.5 MB.
// Shrinking to ~1280px JPEG in the browser keeps uploads small (and detection faster).
function compressImage(file, maxDim = 1280, quality = 0.82) {
  return new Promise((resolve) => {
    if (!file.type || !file.type.startsWith("image/")) return resolve(file);
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      try {
        const scale = Math.min(1, maxDim / Math.max(img.naturalWidth, img.naturalHeight));
        const canvas = document.createElement("canvas");
        canvas.width = Math.round(img.naturalWidth * scale);
        canvas.height = Math.round(img.naturalHeight * scale);
        canvas.getContext("2d").drawImage(img, 0, 0, canvas.width, canvas.height);
        canvas.toBlob(
          (blob) => {
            URL.revokeObjectURL(url);
            resolve(blob && blob.size < file.size ? new File([blob], "photo.jpg", { type: "image/jpeg" }) : file);
          },
          "image/jpeg",
          quality
        );
      } catch {
        URL.revokeObjectURL(url);
        resolve(file);
      }
    };
    img.onerror = () => { URL.revokeObjectURL(url); resolve(file); };
    img.src = url;
  });
}

detectBtn.addEventListener("click", async () => {
  if (!selectedFile) return;
  detectBtn.disabled = true;
  detectBtn.textContent = "Looking at your photo…";
  visionHint.className = "hint";
  visionHint.textContent = "";

  try {
    const photo = await compressImage(selectedFile);
    if (photo.size > 4 * 1024 * 1024) {
      throw new Error("That photo is too large. Please pick a smaller one.");
    }
    const form = new FormData();
    form.append("photo", photo);

    const { detected } = await api("/api/detect-ingredients", { method: "POST", body: form });
    if (detected.length === 0) {
      visionHint.textContent = "Didn't spot anything clearly — try adding ingredients manually below.";
    } else {
      detected.forEach((i) => stagedIngredients.add(i.toLowerCase()));
      renderStagedChips();
      visionHint.className = "hint success";
      visionHint.textContent = `Found ${detected.length} item${detected.length === 1 ? "" : "s"}. Review the list below and add anything missing.`;
    }
  } catch (err) {
    visionHint.className = "hint error";
    visionHint.textContent = err.message;
  } finally {
    detectBtn.disabled = false;
    detectBtn.textContent = "Detect ingredients";
  }
});

// ===========================================================
// SCAN TAB — manual ingredient entry
// ===========================================================
const ingredientInput = document.getElementById("ingredientInput");
const suggestions = document.getElementById("suggestions");
const ingredientChips = document.getElementById("ingredientChips");

ingredientInput.addEventListener("input", () => {
  const q = ingredientInput.value.trim().toLowerCase();
  if (!q) return hideSuggestions();
  const matches = knownIngredients.filter((i) => i.includes(q) && !stagedIngredients.has(i)).slice(0, 8);
  if (matches.length === 0) return hideSuggestions();
  suggestions.innerHTML = matches
    .map((m) => `<div class="suggestion-item" data-value="${esc(m)}">${esc(titleCase(m))}</div>`)
    .join("");
  suggestions.classList.remove("hidden");
});

suggestions.addEventListener("click", (e) => {
  const item = e.target.closest(".suggestion-item");
  if (!item) return;
  addStagedIngredient(item.dataset.value);
  ingredientInput.value = "";
  hideSuggestions();
  ingredientInput.focus();
});

ingredientInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    const val = ingredientInput.value.trim().toLowerCase();
    if (val) addStagedIngredient(val);
    ingredientInput.value = "";
    hideSuggestions();
  }
});

document.addEventListener("click", (e) => {
  if (!e.target.closest(".ingredient-search")) hideSuggestions();
});

function hideSuggestions() { suggestions.classList.add("hidden"); }

function addStagedIngredient(name) {
  stagedIngredients.add(name.toLowerCase());
  renderStagedChips();
}

function renderStagedChips() {
  if (stagedIngredients.size === 0) {
    ingredientChips.innerHTML = `<span class="pantry-empty">No ingredients added yet.</span>`;
    return;
  }
  ingredientChips.innerHTML = [...stagedIngredients]
    .sort()
    .map((i) => `<span class="chip">${esc(titleCase(i))}<button data-remove="${esc(i)}" aria-label="Remove ${esc(i)}">&times;</button></span>`)
    .join("");
}

ingredientChips.addEventListener("click", (e) => {
  const btn = e.target.closest("[data-remove]");
  if (!btn) return;
  stagedIngredients.delete(btn.dataset.remove);
  renderStagedChips();
});

document.getElementById("clearIngredientsBtn").addEventListener("click", () => {
  stagedIngredients.clear();
  renderStagedChips();
});

document.getElementById("saveToPantryBtn").addEventListener("click", async () => {
  if (stagedIngredients.size === 0) return showToast("Nothing to save yet");
  await api("/api/pantry", { method: "POST", body: JSON.stringify({ names: [...stagedIngredients] }) });
  showToast("Saved to pantry");
  loadPantry();
});

document.getElementById("findRecipesBtn").addEventListener("click", async () => {
  if (stagedIngredients.size === 0) return showToast("Add a few ingredients first");
  showPanel("recipes");
  window.scrollTo({ top: 0 });
  await matchAndRenderRecipes([...stagedIngredients]);
  document.getElementById("matchSourceNote").textContent = "Based on what you just entered (not saved to pantry).";
});

// ===========================================================
// PANTRY TAB
// ===========================================================
async function loadPantry() {
  const { pantry } = await api("/api/pantry");
  document.getElementById("pantryCount").textContent = pantry.length || "";
  const list = document.getElementById("pantryList");
  if (pantry.length === 0) {
    list.innerHTML = `<span class="pantry-empty">Your pantry is empty. Add items from the Scan tab or below.</span>`;
    return;
  }
  list.innerHTML = pantry
    .map((p) => `<span class="chip">${esc(titleCase(p.name))}<button data-pantry-remove="${p.id}" aria-label="Remove">&times;</button></span>`)
    .join("");
}

document.getElementById("pantryList").addEventListener("click", async (e) => {
  const btn = e.target.closest("[data-pantry-remove]");
  if (!btn) return;
  await api(`/api/pantry/${btn.dataset.pantryRemove}`, { method: "DELETE" });
  loadPantry();
});

document.getElementById("pantryQuickAddBtn").addEventListener("click", addPantryQuick);
document.getElementById("pantryQuickAdd").addEventListener("keydown", (e) => {
  if (e.key === "Enter") { e.preventDefault(); addPantryQuick(); }
});

async function addPantryQuick() {
  const input = document.getElementById("pantryQuickAdd");
  const val = input.value.trim();
  if (!val) return;
  await api("/api/pantry", { method: "POST", body: JSON.stringify({ names: [val] }) });
  input.value = "";
  loadPantry();
}

document.getElementById("clearPantryBtn").addEventListener("click", async () => {
  if (!confirm("Clear your entire pantry?")) return;
  await api("/api/pantry", { method: "DELETE" });
  loadPantry();
  showToast("Pantry cleared");
});

// ===========================================================
// RECIPES TAB
// ===========================================================
const ALL_TAGS = ["vegetarian", "vegan", "quick", "breakfast", "dinner", "high-protein", "soup", "salad", "no-cook"];

function renderTagFilters() {
  const row = document.getElementById("tagFilters");
  row.innerHTML = ALL_TAGS.map(
    (t) => `<button class="filter-chip ${activeTagFilters.has(t) ? "active" : ""}" data-tag="${t}">${titleCase(t)}</button>`
  ).join("");
}

document.getElementById("tagFilters").addEventListener("click", (e) => {
  const btn = e.target.closest(".filter-chip");
  if (!btn) return;
  const tag = btn.dataset.tag;
  activeTagFilters.has(tag) ? activeTagFilters.delete(tag) : activeTagFilters.add(tag);
  renderTagFilters();
  renderRecipeGrid();
});

async function matchAndRenderRecipes(ingredientsOverride) {
  renderTagFilters();
  let ingredients = ingredientsOverride;
  if (!ingredients) {
    const { pantry } = await api("/api/pantry");
    ingredients = pantry.map((p) => p.name);
    document.getElementById("matchSourceNote").textContent =
      ingredients.length ? "Based on your saved pantry." : "Your pantry is empty — add ingredients from the Scan tab.";
  }
  const { recipes, external } = await api("/api/recipes/match", {
    method: "POST",
    body: JSON.stringify({ ingredients, include_external: true }),
  });
  currentRecipes = recipes;
  renderRecipeGrid();
  renderExternalGrid(external);
}

function renderExternalGrid(external) {
  const section = document.getElementById("externalSection");
  const grid = document.getElementById("externalGrid");
  if (!external || external.length === 0) {
    section.style.display = "none";
    return;
  }
  section.style.display = "block";
  grid.innerHTML = external.map((r) => extCardHTML(r, "TheMealDB")).join("");
}

function renderRecipeGrid() {
  const grid = document.getElementById("recipeGrid");
  let recipes = currentRecipes;
  if (activeTagFilters.size > 0) {
    recipes = recipes.filter((r) => r.tags.some((t) => activeTagFilters.has(t)));
  }
  if (recipes.length === 0) {
    grid.innerHTML = `<div class="empty-state">No recipes match yet — add more ingredients or clear filters.</div>`;
    return;
  }
  grid.innerHTML = recipes.map(localCardHTML).join("");
  observeLocalImages(grid);
}

document.getElementById("freestyleBtn").addEventListener("click", async () => {
  const btn = document.getElementById("freestyleBtn");
  const resultBox = document.getElementById("freestyleResult");
  const { pantry } = await api("/api/pantry");
  const ingredients = pantry.map((p) => p.name);
  if (ingredients.length === 0) {
    return showToast("Add some pantry ingredients first");
  }
  btn.disabled = true;
  btn.textContent = "Thinking of something…";
  try {
    const recipe = await api("/api/ai/freestyle-recipe", { method: "POST", body: JSON.stringify({ ingredients }) });
    resultBox.innerHTML = `
      <div class="card">
        <h3>${esc(recipe.name)}</h3>
        <div class="recipe-meta"><span>${recipe.cook_time} min</span><span>${recipe.servings} servings</span></div>
        <div class="modal-section"><h4>Ingredients</h4><ul class="ingredient-list">${recipe.ingredients.map((i) => `<li>${esc(titleCase(i))}</li>`).join("")}</ul></div>
        <div class="modal-section"><h4>Instructions</h4><ol class="steps-list">${recipe.instructions.map((s) => `<li>${esc(s)}</li>`).join("")}</ol></div>
        <div class="modal-actions">
          <button class="btn btn-primary" id="openFreestyleBtn">Open full recipe</button>
          <button class="btn btn-ghost" id="pdfBtnFreestyle">Download PDF</button>
        </div>
      </div>`;
    document.getElementById("openFreestyleBtn").addEventListener("click", () => {
      showRecipePage(aiModel(recipe, "AI-generated recipe idea from your pantry ingredients"));
    });
    document.getElementById("pdfBtnFreestyle").addEventListener("click", () => {
      downloadCustomPdf(recipe, "AI-generated recipe idea from your pantry ingredients");
    });
  } catch (err) {
    resultBox.innerHTML = `<p class="hint error">${esc(err.message)}</p>`;
  } finally {
    btn.disabled = false;
    btn.textContent = "Get an AI recipe idea";
  }
});

// ===========================================================
// EXPLORE TAB — categories (free TheMealDB)
// ===========================================================
let exploreLoaded = false;

async function openCategory(name) {
  try {
    const { recipes } = await api(`/api/explore/by-category/${encodeURIComponent(name)}`);
    switchTab("explore");
    showExploreResults(`${name} recipes`, recipes.map((r) => ({ ...r, category: name })));
  } catch (err) {
    showToast(err.message);
  }
}

async function loadExplore() {
  if (exploreLoaded) return;
  exploreLoaded = true;

  const catGrid = document.getElementById("categoryGrid");
  try {
    const { categories } = await api("/api/explore/categories");
    catGrid.innerHTML = categories.length
      ? categoryCardsHTML(categories)
      : `<p class="muted">Couldn't reach TheMealDB right now — check your internet connection.</p>`;
    if (!categories.length) exploreLoaded = false;
  } catch {
    exploreLoaded = false;
    catGrid.innerHTML = `<p class="muted">Couldn't load categories.</p>`;
  }
}

document.getElementById("categoryGrid").addEventListener("click", (e) => {
  const card = e.target.closest("[data-category]");
  if (!card) return;
  openCategory(card.dataset.category);
});

function showExploreResults(title, recipes) {
  const wrap = document.getElementById("exploreResultsWrap");
  document.getElementById("exploreResultsTitle").textContent = title;
  const grid = document.getElementById("exploreResultsGrid");
  grid.innerHTML = recipes.length
    ? recipes.map((r) => extCardHTML(r)).join("")
    : `<p class="muted">No recipes found.</p>`;
  wrap.classList.remove("hidden");
  wrap.scrollIntoView({ behavior: "smooth", block: "start" });
}

// ===========================================================
// "HOW TO COOK?" quick search
// ===========================================================
const howToCookOverlay = document.getElementById("howToCookOverlay");
const howToCookInput = document.getElementById("howToCookInput");
const howToCookResults = document.getElementById("howToCookResults");
const htcStatus = document.getElementById("htcStatus");

document.getElementById("howToCookBtn").addEventListener("click", () => {
  howToCookOverlay.classList.remove("hidden");
  howToCookResults.innerHTML = "";
  htcStatus.innerHTML = "";
  howToCookInput.value = "";
  howToCookInput.focus();
});

document.getElementById("howToCookClose").addEventListener("click", () => howToCookOverlay.classList.add("hidden"));
howToCookOverlay.addEventListener("click", (e) => { if (e.target === howToCookOverlay) howToCookOverlay.classList.add("hidden"); });

document.querySelectorAll(".htc-chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    howToCookInput.value = chip.dataset.try;
    runHowToCookSearch(chip.dataset.try);
  });
});

document.getElementById("howToCookSearchBtn").addEventListener("click", () => runHowToCookSearch(howToCookInput.value));
howToCookInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") { e.preventDefault(); runHowToCookSearch(howToCookInput.value); }
});

async function runHowToCookSearch(query) {
  query = query.trim();
  if (!query) return;
  htcStatus.innerHTML = "";
  howToCookResults.innerHTML = `<p class="muted">Searching…</p>`;

  const { local, external } = await api(`/api/how-to-cook/search?q=${encodeURIComponent(query)}`);
  const all = [
    ...local.map((r) => ({ ...r, kind: "local" })),
    ...external.map((r) => ({ ...r, kind: "external" })),
  ];

  if (all.length === 0) {
    howToCookResults.innerHTML = `
      <div class="htc-ai-fallback">
        <p class="muted" style="margin-bottom:10px;">No exact match found — want AI to write the full recipe for "${esc(query)}"?</p>
        <button class="btn btn-accent" id="htcAiBtn">Generate with AI</button>
      </div>`;
    document.getElementById("htcAiBtn").addEventListener("click", () => generateHowToCookAi(query));
    return;
  }

  howToCookResults.innerHTML = all
    .map((r, i) => `
      <div class="htc-result-item" data-index="${i}">
        ${r.thumbnail ? `<img src="${esc(r.thumbnail)}" alt="${esc(r.name)}">` : `<span class="htc-result-noimg">No image</span>`}
        <div>
          <div class="htc-result-name">${esc(r.name)}</div>
          <div class="htc-result-source">${r.kind === "local" ? "Built-in recipe" : "TheMealDB"}</div>
        </div>
      </div>`)
    .join("") +
    `<div class="htc-ai-fallback">
      <p class="muted" style="margin-bottom:10px;">Not quite what you wanted?</p>
      <button class="btn btn-ghost" id="htcAiBtn">Generate "${esc(query)}" with AI instead</button>
    </div>`;

  howToCookResults.querySelectorAll(".htc-result-item").forEach((el) => {
    el.addEventListener("click", () => {
      const item = all[Number(el.dataset.index)];
      howToCookOverlay.classList.add("hidden");
      if (item.kind === "local") openLocalRecipe(item.id);
      else openExternalRecipe(item.external_id);
    });
  });
  document.getElementById("htcAiBtn").addEventListener("click", () => generateHowToCookAi(query));
}

async function generateHowToCookAi(dishName) {
  // Status goes in its own box, so the search results above stay visible and clickable
  htcStatus.innerHTML = `<p class="muted" style="margin-bottom:12px;">AI chef is writing the recipe…</p>`;
  try {
    const recipe = await api("/api/how-to-cook/ai", { method: "POST", body: JSON.stringify({ dish_name: dishName }) });
    htcStatus.innerHTML = "";
    howToCookOverlay.classList.add("hidden");
    showRecipePage(aiModel(recipe, "AI-generated recipe"));
  } catch (err) {
    htcStatus.innerHTML = `
      <div class="htc-error">
        <p>${esc(err.message)}</p>
        <button class="btn btn-accent btn-small" id="htcRetryBtn">Try again</button>
      </div>`;
    document.getElementById("htcRetryBtn").addEventListener("click", () => generateHowToCookAi(dishName));
  }
}

// ===========================================================
// FAVORITES TAB
// ===========================================================
async function loadFavorites() {
  const { recipes } = await api("/api/favorites");
  const grid = document.getElementById("favoritesGrid");
  if (recipes.length === 0) {
    grid.innerHTML = `<div class="empty-state">No saved recipes yet — save one from its recipe page.</div>`;
    return;
  }
  const { pantry } = await api("/api/pantry");
  const have = new Set(pantry.map((p) => p.name));
  const scored = recipes.map((r) => {
    const needed = new Set(r.ingredients);
    const matched = [...needed].filter((i) => have.has(i));
    const missing = [...needed].filter((i) => !have.has(i));
    return { ...r, id: String(r.id), match_percent: Math.round((100 * matched.length) / needed.size), missing_ingredients: missing };
  });
  grid.innerHTML = scored.map(localCardHTML).join("");
  observeLocalImages(grid);
}

// ===========================================================
// SCAN TAB — "jump to a saved recipe" dropdown
// ===========================================================
async function loadSavedRecipesDropdown() {
  const dropdown = document.getElementById("savedRecipesDropdown");
  if (!dropdown) return;
  try {
    const { recipes } = await api("/api/favorites");
    dropdown.innerHTML =
      `<option value="">Your saved recipes…</option>` +
      recipes.map((r) => `<option value="${esc(r.id)}">${esc(r.name)}</option>`).join("");
  } catch {
    /* not fatal — leave the placeholder option */
  }
}

document.getElementById("savedRecipesDropdown").addEventListener("change", (e) => {
  const id = e.target.value;
  if (!id) return;
  openLocalRecipe(id);
  e.target.value = "";
});

// ===========================================================
// RECIPE DETAIL PAGE
// (photo on the right, ingredients card with green ticks, numbered
// "How to make it" steps on the left)
// ===========================================================
const recipeContent = document.getElementById("recipeContent");
let currentRecipeModel = null;

function cleanSteps(list) {
  return (list || [])
    .map((s) => String(s).trim())
    .filter((s) => s && !/^step\s*\d+\s*$/i.test(s))
    .map((s) => s.replace(/^\s*(step\s*)?\d+\s*[.):-]\s*/i, ""))
    .filter(Boolean);
}

function withArticle(word) {
  return (/^[aeiou]/i.test(word) ? "An " : "A ") + word;
}

function externalModel(r) {
  const steps = cleanSteps(r.instructions);
  const bits = [
    r.area && r.area !== "Unknown" ? r.area : null,
    r.category && r.category !== "Miscellaneous" ? r.category.toLowerCase() : null,
  ].filter(Boolean);
  const lead = bits.length ? `${withArticle(bits.join(" "))} recipe` : "A recipe";
  return {
    kind: "external",
    name: r.name,
    image: r.thumbnail,
    description: `${lead} made with ${r.ingredients.length} ingredients. Follow the ${steps.length} steps below.`,
    meta: [
      { k: "Category", v: r.category },
      { k: "Cuisine", v: r.area && r.area !== "Unknown" ? r.area : null },
      { k: "Ingredients", v: r.ingredients.length },
      { k: "Steps", v: steps.length },
    ],
    tags: [],
    ingredients: r.ingredients.map((i) => ({ name: i.name, measure: i.measure, have: true })),
    steps,
    sourceHtml: r.source_url
      ? `Source: <a href="${esc(r.source_url)}" target="_blank" rel="noopener">TheMealDB</a>`
      : "",
    pdfNote: "Source: TheMealDB (free public recipe database)",
  };
}

function aiModel(recipe, note) {
  const ingredients = (recipe.ingredients || []).map((i) => (typeof i === "string" ? { name: i, measure: "" } : i));
  return {
    kind: "ai",
    name: recipe.name,
    image: null,
    description: `${note}. ${ingredients.length} ingredients, ${recipe.instructions.length} steps.`,
    meta: [
      { k: "Cook time", v: recipe.cook_time ? `${recipe.cook_time} min` : null },
      { k: "Servings", v: recipe.servings || null },
      { k: "Ingredients", v: ingredients.length },
      { k: "Steps", v: recipe.instructions.length },
    ],
    tags: recipe.tags || [],
    ingredients: ingredients.map((i) => ({ ...i, have: true })),
    steps: cleanSteps(recipe.instructions),
    sourceHtml: esc(note),
    pdfNote: note,
    pdfExtra: { cook_time: recipe.cook_time, servings: recipe.servings, tags: recipe.tags },
  };
}

function localModel(recipe, isFav) {
  const matched = recipe.matched_ingredients || [];
  const tagText = (recipe.tags || []).slice(0, 2).map((t) => t.toLowerCase()).join(", ");
  return {
    kind: "local",
    id: recipe.id,
    name: recipe.name,
    image: null,
    matchPercent: recipe.match_percent,
    isFav,
    description: `${tagText ? withArticle(tagText) + " recipe" : "A recipe"} made with ${recipe.ingredients.length} ingredients. You already have ${matched.length} of them in your pantry.`,
    meta: [
      { k: "Cook time", v: `${recipe.cook_time} min` },
      { k: "Servings", v: recipe.servings },
      { k: "Ingredients", v: recipe.ingredients.length },
      { k: "Pantry match", v: `${recipe.match_percent}%` },
    ],
    tags: recipe.tags || [],
    ingredients: recipe.ingredients.map((ing) => ({ name: ing, measure: "", have: matched.includes(ing) })),
    steps: recipe.instructions,
  };
}

async function openLocalRecipe(id) {
  try {
    const recipe = await api(`/api/recipes/${encodeURIComponent(id)}`);
    const favs = await api("/api/favorites");
    const isFav = favs.recipes.some((r) => String(r.id) === String(recipe.id));
    showRecipePage(localModel(recipe, isFav));
  } catch (err) {
    showToast(err.message);
  }
}

async function openExternalRecipe(extId) {
  try {
    const recipe = await api(`/api/recipes/external/${encodeURIComponent(extId)}`);
    showRecipePage(externalModel(recipe));
  } catch (err) {
    showToast(err.message);
  }
}

function showRecipePage(m) {
  if (currentTab !== "recipe") {
    recipePrevTab = currentTab;
    recipePrevScroll = window.scrollY;
  }
  currentRecipeModel = m;

  const ingredientItems = m.ingredients
    .map((ing) => {
      const label = m.kind === "local"
        ? esc(titleCase(ing.name))
        : `${ing.measure ? `<span class="measure">${esc(ing.measure)}</span> ` : ""}${esc(titleCase(ing.name))}`;
      const swap = m.kind === "local" && !ing.have
        ? `<button class="sub-btn" data-sub="${esc(ing.name)}" data-recipe-name="${esc(m.name)}">swap?</button>` : "";
      return `<li class="${ing.have ? "have" : "missing"}"><span>${label}${swap}</span></li>`;
    })
    .join("");

  const metaHtml = m.meta
    .filter((x) => x.v !== null && x.v !== undefined && x.v !== "")
    .map((x) => `<div><span>${esc(x.k)}</span><strong>${esc(x.v)}</strong></div>`)
    .join("");

  const tagsHtml = (m.tags || []).length
    ? `<div class="rp-tags">${m.tags.map((t) => `<span class="recipe-tag">${esc(titleCase(t))}</span>`).join("")}</div>` : "";

  const photoHtml = m.image
    ? `<img src="${esc(m.image)}" alt="${esc(m.name)}">`
    : `<span class="noimg">${esc(m.name)}</span>`;

  const isLocal = m.kind === "local";
  const actions = isLocal
    ? `<button class="btn btn-accent" id="rpFav">${m.isFav ? "Saved" : "Save recipe"}</button>
       <button class="btn btn-primary" id="rpCookMode">Cook mode</button>
       <a class="btn btn-ghost" href="/api/recipes/${encodeURIComponent(m.id)}/pdf" target="_blank" rel="noopener">Download PDF</a>
       <button class="btn btn-ghost" id="rpPrint">Print</button>
       <button class="btn btn-ghost" id="rpCooked">Mark as cooked</button>`
    : `<button class="btn btn-primary" id="rpCookMode">Cook mode</button>
       <button class="btn btn-ghost" id="rpPdf">Download PDF</button>
       <button class="btn btn-ghost" id="rpPrint">Print</button>`;

  recipeContent.innerHTML = `
    <button class="back-link" id="rpBack">&larr; Back</button>
    <div class="rp">
      <div class="rp-main">
        <h1 class="rp-title">${esc(m.name)}</h1>
        <div class="rp-meta">${metaHtml}</div>
        <p class="rp-desc">${esc(m.description)}</p>
        ${tagsHtml}
        <div class="rp-actions">${actions}</div>

        <h2 class="rp-h">How to make it</h2>
        <ol class="rp-steps">${m.steps.map((s) => `<li><span>${esc(s)}</span></li>`).join("")}</ol>

        ${isLocal ? `
        <h2 class="rp-h">Nutrition per serving <button class="sub-btn" id="rpNutriBtn">estimate with AI</button></h2>
        <div id="rpNutriBox"></div>` : ""}

        ${m.sourceHtml ? `<p class="hint">${m.sourceHtml}</p>` : ""}
      </div>

      <aside class="rp-side">
        <div class="rp-photo" id="rpPhoto">${photoHtml}</div>
        <div class="rp-ingredients">
          <h3>Ingredients</h3>
          <p class="muted">${m.ingredients.length} items${isLocal ? " — green ones are already in your pantry" : ""}</p>
          <ul class="rp-ing-list">${ingredientItems}</ul>
          ${isLocal ? `<button class="btn btn-ghost btn-small" id="rpShop">Add to shopping list</button>` : ""}
          <p class="hint" id="rpHint"></p>
        </div>
      </aside>
    </div>`;

  bindRecipePage(m);
  showPanel("recipe");
  window.scrollTo({ top: 0 });

  // Built-in recipes have no photo of their own — fetch one in the background
  if (isLocal) {
    api(`/api/recipes/${encodeURIComponent(m.id)}/image`)
      .then(({ thumbnail }) => {
        if (!thumbnail || currentRecipeModel !== m) return;
        m.image = thumbnail;
        document.getElementById("rpPhoto").innerHTML = `<img src="${esc(thumbnail)}" alt="${esc(m.name)}">`;
      })
      .catch(() => {});
  }
}

function bindRecipePage(m) {
  document.getElementById("rpBack").addEventListener("click", goBackFromRecipe);
  document.getElementById("rpPrint").addEventListener("click", () => window.print());
  document.getElementById("rpCookMode").addEventListener("click", () => openCookMode(m.name, m.steps));

  const pdfBtn = document.getElementById("rpPdf");
  if (pdfBtn) {
    pdfBtn.addEventListener("click", () => {
      downloadCustomPdf(
        {
          name: m.name,
          ingredients: m.ingredients.map((i) => (i.measure ? `${i.measure} ${i.name}` : i.name)),
          instructions: m.steps,
          ...(m.pdfExtra || {}),
        },
        m.pdfNote
      );
    });
  }

  if (m.kind !== "local") return;

  document.getElementById("rpFav").addEventListener("click", async (e) => {
    const btn = e.currentTarget;
    if (m.isFav) {
      await api(`/api/favorites/${m.id}`, { method: "DELETE" });
      m.isFav = false;
      btn.textContent = "Save recipe";
      showToast("Removed from saved");
    } else {
      await api(`/api/favorites/${m.id}`, { method: "POST" });
      m.isFav = true;
      btn.textContent = "Saved";
      showToast("Saved recipe");
    }
    loadSavedRecipesDropdown();
  });

  document.getElementById("rpShop").addEventListener("click", async () => {
    const list = await api(`/api/recipes/${m.id}/shopping-list`);
    const hint = document.getElementById("rpHint");
    hint.className = "hint";
    hint.textContent = list.missing_ingredients.length
      ? `Shopping list: ${list.missing_ingredients.map(titleCase).join(", ")}`
      : "You already have everything for this recipe!";
  });

  document.getElementById("rpCooked").addEventListener("click", async () => {
    await api(`/api/recipes/${m.id}/cook`, { method: "POST" });
    showToast(`Enjoy your ${m.name}! Used ingredients removed from pantry.`);
    loadPantry();
    switchTab("recipes");
  });

  document.getElementById("rpNutriBtn").addEventListener("click", async (e) => {
    const btn = e.currentTarget;
    btn.textContent = "estimating…";
    btn.disabled = true;
    try {
      const n = await api(`/api/recipes/${m.id}/nutrition`);
      if ([n.calories, n.protein_g, n.carbs_g, n.fat_g].every((v) => v === null || v === undefined)) {
        throw new Error("Couldn't estimate the nutrition this time. Please try again.");
      }
      document.getElementById("rpNutriBox").innerHTML = `
        <div class="nutrition-grid">
          <div class="nutrition-stat"><div class="value">${n.calories ?? "–"}</div><div class="label">Calories</div></div>
          <div class="nutrition-stat"><div class="value">${n.protein_g ?? "–"}g</div><div class="label">Protein</div></div>
          <div class="nutrition-stat"><div class="value">${n.carbs_g ?? "–"}g</div><div class="label">Carbs</div></div>
          <div class="nutrition-stat"><div class="value">${n.fat_g ?? "–"}g</div><div class="label">Fat</div></div>
        </div>`;
      btn.remove();
    } catch (err) {
      btn.textContent = "estimate with AI";
      btn.disabled = false;
      showToast(err.message);
    }
  });
}

function goBackFromRecipe() {
  showPanel(recipePrevTab);
  if (recipePrevTab === "favorites") loadFavorites();
  requestAnimationFrame(() => window.scrollTo({ top: recipePrevScroll }));
}

// AI ingredient substitutions (delegated, since the page re-renders per recipe)
recipeContent.addEventListener("click", async (e) => {
  const subBtn = e.target.closest("[data-sub]");
  if (!subBtn) return;
  subBtn.textContent = "…";
  try {
    const result = await api("/api/ai/substitute", {
      method: "POST",
      body: JSON.stringify({ ingredient: subBtn.dataset.sub, recipe_name: subBtn.dataset.recipeName }),
    });
    const subs = (result.substitutes || []).map((s) => `${s.name} (${s.note})`).join("; ") || "No suggestions found.";
    const box = document.createElement("div");
    box.className = "substitute-result";
    box.textContent = `Try: ${subs}`;
    subBtn.closest("li").appendChild(box);
    subBtn.remove();
  } catch (err) {
    subBtn.textContent = "swap?";
    showToast(err.message);
  }
});

// ===========================================================
// PDF download helper (for recipes not in the local DB, e.g.
// TheMealDB or AI results, which need a POST request)
// ===========================================================
async function downloadCustomPdf(recipe, sourceNote) {
  const res = await fetch(`${API_BASE}/api/recipes/pdf/custom`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: recipe.name,
      cook_time: recipe.cook_time || null,
      servings: recipe.servings || null,
      tags: recipe.tags || [],
      ingredients: recipe.ingredients,
      instructions: recipe.instructions,
      source_note: sourceNote || null,
    }),
  });
  if (!res.ok) return showToast("Could not generate PDF");
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${recipe.name}.pdf`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    closeCookMode();
    howToCookOverlay.classList.add("hidden");
  }
});

// ===========================================================
// COOK MODE — voice-guided steps using the browser's free built-in
// speech synthesis API (no external service, no cost)
// ===========================================================
const cookModeOverlay = document.getElementById("cookModeOverlay");
const cookModeBody = document.getElementById("cookModeBody");
const synth = window.speechSynthesis;

function openCookMode(title, steps) {
  if (!steps || !steps.length) return showToast("No steps to walk through");
  cookModeState = { title, steps, index: 0 };
  renderCookStep();
  cookModeOverlay.classList.remove("hidden");
}

function renderCookStep() {
  const { title, steps, index } = cookModeState;
  const dots = steps.map((_, i) => `<span class="cook-progress-dot ${i < index ? "done" : i === index ? "current" : ""}"></span>`).join("");
  cookModeBody.innerHTML = `
    <h3 style="margin-bottom:4px;">${esc(title)}</h3>
    <p class="muted" style="margin-bottom:16px;">Step ${index + 1} of ${steps.length}</p>
    <div class="cook-progress">${dots}</div>
    <div class="cook-step-num">STEP ${index + 1}</div>
    <div class="cook-step-text">${esc(steps[index])}</div>
    <div class="cook-nav">
      <button class="btn btn-ghost" id="cookPrevBtn" ${index === 0 ? "disabled" : ""}>Back</button>
      <button class="btn btn-accent" id="cookSpeakBtn">Read aloud</button>
      <button class="btn btn-primary" id="cookNextBtn">${index === steps.length - 1 ? "Done" : "Next"}</button>
    </div>
  `;
  document.getElementById("cookPrevBtn").addEventListener("click", () => {
    if (synth) synth.cancel();
    cookModeState.index = Math.max(0, cookModeState.index - 1);
    renderCookStep();
  });
  document.getElementById("cookNextBtn").addEventListener("click", () => {
    if (synth) synth.cancel();
    if (cookModeState.index === steps.length - 1) {
      closeCookMode();
      showToast("Enjoy your meal!");
      return;
    }
    cookModeState.index += 1;
    renderCookStep();
  });
  document.getElementById("cookSpeakBtn").addEventListener("click", () => speakCurrentStep());
}

function speakCurrentStep() {
  if (!synth) return showToast("Voice isn't supported in this browser");
  synth.cancel();
  const utter = new SpeechSynthesisUtterance(cookModeState.steps[cookModeState.index]);
  utter.rate = 0.95;
  synth.speak(utter);
}

document.getElementById("cookModeClose").addEventListener("click", closeCookMode);
cookModeOverlay.addEventListener("click", (e) => { if (e.target === cookModeOverlay) closeCookMode(); });

function closeCookMode() {
  if (synth) synth.cancel();
  cookModeOverlay.classList.add("hidden");
  cookModeBody.innerHTML = "";
  cookModeState = null;
}

// ===========================================================
// VOICE COMMANDS — Web Speech API (browser-native, no service)
// ===========================================================
const SpeechRecognitionCtor = window.SpeechRecognition || window.webkitSpeechRecognition;

function listenOnce(button, onResult) {
  if (!SpeechRecognitionCtor) {
    showToast("Voice input isn't supported in this browser — try Chrome.");
    return;
  }
  const recognition = new SpeechRecognitionCtor();
  recognition.lang = "en-US";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  button.classList.add("listening");
  recognition.start();

  recognition.onresult = (e) => {
    const transcript = e.results[0][0].transcript.trim();
    onResult(transcript);
  };
  recognition.onerror = () => showToast("Didn't catch that — try again.");
  recognition.onend = () => button.classList.remove("listening");
}

// Mic on the ingredient entry field — speaks an ingredient, adds it as a chip
const ingredientMicBtn = document.getElementById("ingredientMicBtn");
if (ingredientMicBtn) {
  ingredientMicBtn.addEventListener("click", () => {
    listenOnce(ingredientMicBtn, (transcript) => {
      transcript
        .toLowerCase()
        .split(/,| and /)
        .map((s) => s.trim())
        .filter(Boolean)
        .forEach((name) => addStagedIngredient(name));
      showToast(`Added "${transcript}"`);
    });
  });
}

// Mic on the "How to Cook?" search — speaks a dish name, runs the search
const howToCookMicBtn = document.getElementById("howToCookMicBtn");
if (howToCookMicBtn) {
  howToCookMicBtn.addEventListener("click", () => {
    listenOnce(howToCookMicBtn, (transcript) => {
      howToCookInput.value = transcript;
      runHowToCookSearch(transcript);
    });
  });
}

// Global voice command button in the header — routes to a tab or
// straight into "How to Cook?" depending on what's said.
const voiceCommandBtn = document.getElementById("voiceCommandBtn");
const TAB_VOICE_ALIASES = {
  home: ["home"],
  scan: ["scan", "camera", "photo"],
  pantry: ["pantry"],
  recipes: ["recipes", "recipe"],
  explore: ["explore", "categories", "cuisine"],
  favorites: ["saved", "favorites", "favourites"],
};

if (voiceCommandBtn) {
  voiceCommandBtn.addEventListener("click", () => {
    listenOnce(voiceCommandBtn, (transcript) => {
      const heard = transcript.toLowerCase();
      const cookMatch = heard.match(/^(how to cook|cook|make|show me)\s+(.+)/);
      if (cookMatch) {
        document.getElementById("howToCookBtn").click();
        setTimeout(() => {
          howToCookInput.value = cookMatch[2];
          runHowToCookSearch(cookMatch[2]);
        }, 50);
        return;
      }
      for (const [tab, aliases] of Object.entries(TAB_VOICE_ALIASES)) {
        if (aliases.some((a) => heard.includes(a))) {
          switchTab(tab);
          showToast(`Opened ${titleCase(tab)}`);
          return;
        }
      }
      showToast(`Heard "${transcript}" — try "scan", "pantry", "recipes", or "how to cook <dish>".`);
    });
  });
}
