/**
 * Rustic Recipe Card Maker & Storage Application Controller
 * Handles Recipe Box, Ayurvedic & Nutritional Ingredients Pantry, and Live Card Workbench
 */

// Application State
const AppState = {
  currentView: "catalog", // "catalog", "ingredients", or "maker"
  recipes: [],
  ingredients: [],
  activeRecipe: null,
  cardPreset: "size-3x5",
  cardScale: 1.0,
  isEditing: false,
};

// DOM Cache
const DOM = {};

document.addEventListener("DOMContentLoaded", async () => {
  initDOM();
  attachEventListeners();
  await loadPantryIngredients();
  await loadRecipes();

  // URL Hash routing
  if (window.location.hash === "#maker" || window.location.hash === "#new") {
    switchView("maker");
    createNewRecipe();
  } else if (window.location.hash === "#ingredients" || window.location.hash === "#pantry") {
    switchView("ingredients");
  }
});

function initDOM() {
  // Navigation & Views
  DOM.btnNavCatalog = document.getElementById("btnNavCatalog");
  DOM.btnNavIngredients = document.getElementById("btnNavIngredients");
  DOM.btnNavMaker = document.getElementById("btnNavMaker");
  DOM.catalogView = document.getElementById("catalogView");
  DOM.ingredientsView = document.getElementById("ingredientsView");
  DOM.makerView = document.getElementById("makerView");

  // Recipe Catalog View Elements
  DOM.searchInput = document.getElementById("searchInput");
  DOM.categoryFilter = document.getElementById("categoryFilter");
  DOM.catalogGrid = document.getElementById("catalogGrid");
  DOM.catalogCount = document.getElementById("catalogCount");
  DOM.pantryCount = document.getElementById("pantryCount");

  // Ingredients Pantry View Elements
  DOM.ingSearchInput = document.getElementById("ingSearchInput");
  DOM.ingCategoryFilter = document.getElementById("ingCategoryFilter");
  DOM.ingredientsGrid = document.getElementById("ingredientsGrid");
  DOM.btnOpenAddIngredientModal = document.getElementById("btnOpenAddIngredientModal");

  // Ingredient Modal Elements
  DOM.ingredientModal = document.getElementById("ingredientModal");
  DOM.ingredientModalTitle = document.getElementById("ingredientModalTitle");
  DOM.btnIngredientModalClose = document.getElementById("btnIngredientModalClose");
  DOM.btnIngredientModalCancel = document.getElementById("btnIngredientModalCancel");
  DOM.btnIngredientModalSave = document.getElementById("btnIngredientModalSave");
  DOM.modalIngId = document.getElementById("modalIngId");
  DOM.modalIngNameEn = document.getElementById("modalIngNameEn");
  DOM.modalIngNameHi = document.getElementById("modalIngNameHi");
  DOM.modalIngNameMr = document.getElementById("modalIngNameMr");
  DOM.modalIngCategory = document.getElementById("modalIngCategory");
  DOM.modalIngCalories = document.getElementById("modalIngCalories");
  DOM.modalIngZinc = document.getElementById("modalIngZinc");
  DOM.modalIngIron = document.getElementById("modalIngIron");
  DOM.modalIngCalcium = document.getElementById("modalIngCalcium");
  DOM.modalIngProtein = document.getElementById("modalIngProtein");
  DOM.modalIngFiber = document.getElementById("modalIngFiber");
  DOM.modalIngMicro = document.getElementById("modalIngMicro");
  DOM.modalIngDosha = document.getElementById("modalIngDosha");
  DOM.modalIngRasa = document.getElementById("modalIngRasa");
  DOM.modalIngVirya = document.getElementById("modalIngVirya");
  DOM.modalIngAyurveda = document.getElementById("modalIngAyurveda");

  // Maker Toolbar & Controls
  DOM.btnSaveRecipe = document.getElementById("btnSaveRecipe");
  DOM.btnExportJpg = document.getElementById("btnExportJpg");
  DOM.btnPrintCard = document.getElementById("btnPrintCard");
  DOM.btnResetForm = document.getElementById("btnResetForm");
  DOM.sizeButtons = document.querySelectorAll(".size-btn");
  DOM.scaleSlider = document.getElementById("scaleSlider");
  DOM.scaleValueText = document.getElementById("scaleValueText");

  // Live Card Preview Elements
  DOM.recipeCard = document.getElementById("recipeCard");
  DOM.cardPhotoImg = document.getElementById("cardPhotoImg");
  DOM.cardPhotoWrapper = document.getElementById("cardPhotoWrapper");
  DOM.cardTitle = document.getElementById("cardTitle");
  DOM.cardCategoryBadge = document.getElementById("cardCategoryBadge");
  DOM.cardServings = document.getElementById("cardServings");
  DOM.cardYieldGrams = document.getElementById("cardYieldGrams");
  DOM.cardPrepTime = document.getElementById("cardPrepTime");
  DOM.cardTotalTime = document.getElementById("cardTotalTime");
  DOM.cardIngredientsList = document.getElementById("cardIngredientsList");
  DOM.cardMethodSteps = document.getElementById("cardMethodSteps");
  DOM.cardNutrientsRow = document.getElementById("cardNutrientsRow");
  DOM.cardCalories = document.getElementById("cardCalories");
  DOM.cardProtein = document.getElementById("cardProtein");
  DOM.cardCarbs = document.getElementById("cardCarbs");
  DOM.cardFat = document.getElementById("cardFat");

  // Micronutrients & Ayurvedic Ribbon
  DOM.cardMicroNutrientsRow = document.getElementById("cardMicroNutrientsRow");
  DOM.cardIronPill = document.getElementById("cardIronPill");
  DOM.cardIronVal = document.getElementById("cardIronVal");
  DOM.cardZincPill = document.getElementById("cardZincPill");
  DOM.cardZincVal = document.getElementById("cardZincVal");
  DOM.cardAyurvedicBadge = document.getElementById("cardAyurvedicBadge");
  DOM.cardAyurText = document.getElementById("cardAyurText");

  // Editor Form Inputs
  DOM.recipeForm = document.getElementById("recipeForm");
  DOM.formRecipeId = document.getElementById("formRecipeId");
  DOM.formTitle = document.getElementById("formTitle");
  DOM.formCategory = document.getElementById("formCategory");
  DOM.formServings = document.getElementById("formServings");
  DOM.formYieldGrams = document.getElementById("formYieldGrams");
  DOM.formPrepTime = document.getElementById("formPrepTime");
  DOM.formCookTime = document.getElementById("formCookTime");
  DOM.formTotalTime = document.getElementById("formTotalTime");
  DOM.formCalories = document.getElementById("formCalories");
  DOM.formProtein = document.getElementById("formProtein");
  DOM.formCarbs = document.getElementById("formCarbs");
  DOM.formFat = document.getElementById("formFat");
  DOM.formIron = document.getElementById("formIron");
  DOM.formZinc = document.getElementById("formZinc");
  DOM.formFiber = document.getElementById("formFiber");
  DOM.formAyurvedicNote = document.getElementById("formAyurvedicNote");
  DOM.formDescription = document.getElementById("formDescription");
  DOM.formNotes = document.getElementById("formNotes");
  DOM.formImageUrl = document.getElementById("formImageUrl");
  DOM.imageFileInput = document.getElementById("imageFileInput");

  // Ingredients and Steps Editor Lists
  DOM.ingredientsEditorList = document.getElementById("ingredientsEditorList");
  DOM.btnAddIngredient = document.getElementById("btnAddIngredient");
  DOM.stepsEditorList = document.getElementById("stepsEditorList");
  DOM.btnAddStep = document.getElementById("btnAddStep");

  // Print Modal
  DOM.printModal = document.getElementById("printModal");
  DOM.btnPrintConfirm = document.getElementById("btnPrintConfirm");
  DOM.btnPrintCancel = document.getElementById("btnPrintCancel");
  DOM.printModeSelect = document.getElementById("printModeSelect");
}

function attachEventListeners() {
  // Top Navigation View Switching
  DOM.btnNavCatalog.addEventListener("click", () => switchView("catalog"));
  DOM.btnNavIngredients.addEventListener("click", () => switchView("ingredients"));
  DOM.btnNavMaker.addEventListener("click", () => {
    switchView("maker");
    if (!AppState.activeRecipe) {
      createNewRecipe();
    }
  });

  // Recipe Box Search & Category Filter
  DOM.searchInput.addEventListener("input", debounce(filterCatalog, 200));
  DOM.categoryFilter.addEventListener("change", filterCatalog);

  // Ingredients Pantry Search & Category Filter
  DOM.ingSearchInput.addEventListener("input", debounce(filterIngredientsCatalog, 200));
  DOM.ingCategoryFilter.addEventListener("change", filterIngredientsCatalog);

  // Ingredient Modal Handlers
  DOM.btnOpenAddIngredientModal.addEventListener("click", () => openAddIngredientModal());
  DOM.btnIngredientModalClose.addEventListener("click", closeIngredientModal);
  DOM.btnIngredientModalCancel.addEventListener("click", closeIngredientModal);
  DOM.btnIngredientModalSave.addEventListener("click", saveIngredientModal);

  // Card Size Preset Buttons
  DOM.sizeButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      DOM.sizeButtons.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const size = btn.dataset.size;
      setCardSize(size);
    });
  });

  // Zoom Scale Slider
  DOM.scaleSlider.addEventListener("input", (e) => {
    const scale = parseFloat(e.target.value);
    AppState.cardScale = scale;
    DOM.recipeCard.style.transform = `scale(${scale})`;
    DOM.scaleValueText.textContent = `${Math.round(scale * 100)}%`;
  });

  // Form Inputs Live Sync
  const syncInputs = [
    [DOM.formTitle, () => syncTitle()],
    [DOM.formCategory, () => syncCategory()],
    [DOM.formServings, () => syncServings()],
    [DOM.formYieldGrams, () => syncServings()],
    [DOM.formPrepTime, () => syncTimes()],
    [DOM.formTotalTime, () => syncTimes()],
    [DOM.formCalories, () => syncNutrients()],
    [DOM.formProtein, () => syncNutrients()],
    [DOM.formCarbs, () => syncNutrients()],
    [DOM.formFat, () => syncNutrients()],
    [DOM.formIron, () => syncMicroNutrients()],
    [DOM.formZinc, () => syncMicroNutrients()],
    [DOM.formAyurvedicNote, () => syncMicroNutrients()],
  ];

  syncInputs.forEach(([input, handler]) => {
    if (input) {
      input.addEventListener("input", handler);
    }
  });

  // Ingredients and Steps Actions
  DOM.btnAddIngredient.addEventListener("click", () => addIngredientRow());
  DOM.btnAddStep.addEventListener("click", () => addStepRow());

  // Image Upload Handlers
  DOM.cardPhotoWrapper.addEventListener("click", () => DOM.imageFileInput.click());
  DOM.imageFileInput.addEventListener("change", handleImageUpload);

  // Drag & drop image to card photo frame
  DOM.cardPhotoWrapper.addEventListener("dragover", (e) => {
    e.preventDefault();
    DOM.cardPhotoWrapper.style.borderColor = "var(--vintage-red)";
  });
  DOM.cardPhotoWrapper.addEventListener("dragleave", () => {
    DOM.cardPhotoWrapper.style.borderColor = "";
  });
  DOM.cardPhotoWrapper.addEventListener("drop", (e) => {
    e.preventDefault();
    DOM.cardPhotoWrapper.style.borderColor = "";
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      uploadImageFile(e.dataTransfer.files[0]);
    }
  });

  // Save recipe
  DOM.btnSaveRecipe.addEventListener("click", saveRecipe);

  // Reset form
  DOM.btnResetForm.addEventListener("click", () => {
    if (confirm("Reset current card to start a fresh recipe?")) {
      createNewRecipe();
    }
  });

  // Export JPG
  DOM.btnExportJpg.addEventListener("click", () => {
    const data = collectFormData();
    CardExporter.exportToJpg(DOM.recipeCard, data);
  });

  // Print Dialog
  DOM.btnPrintCard.addEventListener("click", () => {
    DOM.printModal.classList.add("show");
  });
  DOM.btnPrintCancel.addEventListener("click", () => {
    DOM.printModal.classList.remove("show");
  });
  DOM.btnPrintConfirm.addEventListener("click", () => {
    DOM.printModal.classList.remove("show");
    const mode = DOM.printModeSelect.value;
    CardExporter.printCard(mode);
  });
}

function switchView(viewName) {
  AppState.currentView = viewName;

  // Deactivate all
  DOM.catalogView.classList.remove("active");
  DOM.ingredientsView.classList.remove("active");
  DOM.makerView.classList.remove("active");

  DOM.btnNavCatalog.classList.remove("btn-active");
  DOM.btnNavIngredients.classList.remove("btn-active");
  DOM.btnNavMaker.classList.remove("btn-active");

  if (viewName === "catalog") {
    DOM.catalogView.classList.add("active");
    DOM.btnNavCatalog.classList.add("btn-active");
    loadRecipes();
  } else if (viewName === "ingredients") {
    DOM.ingredientsView.classList.add("active");
    DOM.btnNavIngredients.classList.add("btn-active");
    loadPantryIngredients();
  } else {
    DOM.makerView.classList.add("active");
    DOM.btnNavMaker.classList.add("btn-active");
  }
}

function setCardSize(sizeClass) {
  AppState.cardPreset = sizeClass;
  DOM.recipeCard.classList.remove("size-3x5", "size-4x6", "size-5x7");
  DOM.recipeCard.classList.add(sizeClass);
}

// ------------------------------------------------------------------------------
// API & DATA OPERATIONS: PANTRY INGREDIENTS
// ------------------------------------------------------------------------------

async function loadPantryIngredients() {
  try {
    const res = await fetch("/api/ingredients");
    const data = await res.json();
    AppState.ingredients = data.ingredients || [];
    if (DOM.pantryCount) {
      DOM.pantryCount.textContent = AppState.ingredients.length;
    }
    renderIngredientsCatalog(AppState.ingredients);
  } catch (err) {
    console.error("Failed to load ingredients:", err);
  }
}

function filterIngredientsCatalog() {
  const query = DOM.ingSearchInput.value.toLowerCase().trim();
  const category = DOM.ingCategoryFilter.value;

  const filtered = AppState.ingredients.filter((ing) => {
    const matchesQuery =
      !query ||
      (ing.name_en && ing.name_en.toLowerCase().includes(query)) ||
      (ing.name_hi && ing.name_hi.toLowerCase().includes(query)) ||
      (ing.name_mr && ing.name_mr.toLowerCase().includes(query)) ||
      (ing.ayurvedic_significance && ing.ayurvedic_significance.toLowerCase().includes(query)) ||
      (ing.micronutrients && ing.micronutrients.toLowerCase().includes(query)) ||
      (ing.zinc && ing.zinc.toLowerCase().includes(query)) ||
      (ing.iron && ing.iron.toLowerCase().includes(query)) ||
      (ing.dosha_effect && ing.dosha_effect.toLowerCase().includes(query));

    const matchesCat = !category || category === "all" || ing.category === category;
    return matchesQuery && matchesCat;
  });

  renderIngredientsCatalog(filtered);
}

function renderIngredientsCatalog(ingredients) {
  DOM.ingredientsGrid.innerHTML = "";

  if (ingredients.length === 0) {
    DOM.ingredientsGrid.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 3rem; color: #cbbaa5;">
        <p style="font-size: 1.2rem; margin-bottom: 0.5rem;">🌿 No pantry ingredients matched</p>
        <p style="font-size: 0.9rem; font-style: italic;">Try searching in English, Hindi (हल्दी), or Marathi (हळद), or add a new custom ingredient!</p>
      </div>
    `;
    return;
  }

  ingredients.forEach((ing) => {
    const card = document.createElement("div");
    card.className = "ingredient-card-item";
    const nutritionBasis = ing.nutrition_basis || "per 100 g ingredient";
    const basisAmount = nutritionBasis.replace(/^per\s+/i, "");

    const hiBadge = ing.name_hi
      ? `<span class="badge-lang badge-hi devanagari-font" title="Hindi">🇮🇳 ${escapeHtml(ing.name_hi)}</span>`
      : "";
    const mrBadge = ing.name_mr
      ? `<span class="badge-lang badge-mr devanagari-font" title="Marathi">🚩 ${escapeHtml(ing.name_mr)}</span>`
      : "";

    const doshaPill = ing.dosha_effect
      ? `<span class="dosha-tag">${escapeHtml(ing.dosha_effect)}</span>`
      : "";
    const rasaTag = ing.taste_rasa
      ? `<span class="ayur-prop-tag">Rasa: ${escapeHtml(ing.taste_rasa)}</span>`
      : "";
    const viryaTag = ing.potency_virya
      ? `<span class="ayur-prop-tag">Virya: ${escapeHtml(ing.potency_virya)}</span>`
      : "";

    card.innerHTML = `
      <div class="ing-header">
        <div>
          <h3 class="ing-name-en">${escapeHtml(ing.name_en)}</h3>
          <div class="ing-lang-badges">
            ${hiBadge}
            ${mrBadge}
          </div>
        </div>
        <span class="ing-category-tag">${escapeHtml(ing.category || "General")}</span>
      </div>

      <!-- Ayurvedic Significance & Properties -->
      <div class="ing-ayur-box">
        <div class="ing-dosha-row">
          ${doshaPill}
          ${rasaTag}
          ${viryaTag}
        </div>
        <p class="ing-ayur-desc">${escapeHtml(ing.ayurvedic_significance || "Nourishing and restorative culinary ingredient.")}</p>
      </div>

      <div class="ing-nutrition-basis">
        <span>Nutrition basis: <b>${escapeHtml(nutritionBasis)}</b></span>
        <strong>Every ${escapeHtml(basisAmount)} contains:</strong>
      </div>
      <!-- Nutritional Profile (Zinc, Iron, Calcium, Calories, Protein, Fiber) -->
      <div class="ing-nutrient-grid">
        <div class="ing-nutr-item">
          <span class="ing-nutr-lbl">⚡ Zinc</span>
          <span class="ing-nutr-val highlight-zinc">${escapeHtml(ing.zinc || "-")}</span>
        </div>
        <div class="ing-nutr-item">
          <span class="ing-nutr-lbl">🩸 Iron</span>
          <span class="ing-nutr-val highlight-iron">${escapeHtml(ing.iron || "-")}</span>
        </div>
        <div class="ing-nutr-item">
          <span class="ing-nutr-lbl">🦴 Calcium</span>
          <span class="ing-nutr-val">${escapeHtml(ing.calcium || "-")}</span>
        </div>
        <div class="ing-nutr-item">
          <span class="ing-nutr-lbl">⚡ Energy</span>
          <span class="ing-nutr-val">${escapeHtml(ing.calories_per_100g || "-")}</span>
        </div>
        <div class="ing-nutr-item">
          <span class="ing-nutr-lbl">🥩 Protein</span>
          <span class="ing-nutr-val">${escapeHtml(ing.protein || "-")}</span>
        </div>
        <div class="ing-nutr-item">
          <span class="ing-nutr-lbl">🌾 Fiber</span>
          <span class="ing-nutr-val">${escapeHtml(ing.fiber || "-")}</span>
        </div>
      </div>

      ${ing.micronutrients ? `<div class="ing-micro-text"><b>Active Elements:</b> ${escapeHtml(ing.micronutrients)}</div>` : ""}

      <!-- Actions -->
      <div class="ing-actions-row">
        <button type="button" class="btn-add-to-recipe" data-id="${ing.id}">
          ➕ Add to Recipe Card
        </button>
        <div style="display:flex; gap:0.4rem;">
          <button type="button" class="btn-rustic btn-edit-ing" data-id="${ing.id}" style="padding: 2px 8px; font-size: 0.75rem;">✏️ Edit</button>
          <button type="button" class="btn-rustic btn-del-ing" data-id="${ing.id}" style="padding: 2px 8px; font-size: 0.75rem; color:#c96e62;">🗑️</button>
        </div>
      </div>
    `;

    // Add to Active Recipe Button
    card.querySelector(".btn-add-to-recipe").addEventListener("click", () => {
      addIngredientToCurrentRecipe(ing);
    });

    // Edit Ingredient Button
    card.querySelector(".btn-edit-ing").addEventListener("click", () => {
      openAddIngredientModal(ing);
    });

    // Delete Ingredient Button
    card.querySelector(".btn-del-ing").addEventListener("click", () => {
      deleteIngredientFromPantry(ing.id, ing.name_en);
    });

    DOM.ingredientsGrid.appendChild(card);
  });
}

function addIngredientToCurrentRecipe(ing) {
  if (!AppState.activeRecipe) {
    createNewRecipe();
  }
  switchView("maker");

  // Form displayName with Hindi/Marathi if available
  let displayName = ing.name_en;
  if (ing.name_hi) {
    displayName += ` (${ing.name_hi})`;
  }

  addIngredientRow({
    amount: "1",
    unit: "tsp",
    name: displayName,
    notes: ing.dosha_effect ? ing.dosha_effect : "",
  });

  // Enrich active recipe nutrients if currently empty
  if (!DOM.formIron.value && ing.iron) {
    DOM.formIron.value = ing.iron;
    syncMicroNutrients();
  }
  if (!DOM.formZinc.value && ing.zinc) {
    DOM.formZinc.value = ing.zinc;
    syncMicroNutrients();
  }
  if (!DOM.formAyurvedicNote.value && ing.dosha_effect) {
    DOM.formAyurvedicNote.value = `${ing.dosha_effect} | ${ing.name_en}`;
    syncMicroNutrients();
  }

  alert(`🌿 Added "${displayName}" to your active recipe workbench!`);
}

function openAddIngredientModal(ing = null) {
  if (ing) {
    DOM.ingredientModalTitle.textContent = "✏️ Edit Ayurvedic Ingredient";
    DOM.modalIngId.value = ing.id || "";
    DOM.modalIngNameEn.value = ing.name_en || "";
    DOM.modalIngNameHi.value = ing.name_hi || "";
    DOM.modalIngNameMr.value = ing.name_mr || "";
    DOM.modalIngCategory.value = ing.category || "Spices & Healing Herbs";
    DOM.modalIngCalories.value = ing.calories_per_100g || "";
    DOM.modalIngZinc.value = ing.zinc || "";
    DOM.modalIngIron.value = ing.iron || "";
    DOM.modalIngCalcium.value = ing.calcium || "";
    DOM.modalIngProtein.value = ing.protein || "";
    DOM.modalIngFiber.value = ing.fiber || "";
    DOM.modalIngMicro.value = ing.micronutrients || "";
    DOM.modalIngDosha.value = ing.dosha_effect || "";
    DOM.modalIngRasa.value = ing.taste_rasa || "";
    DOM.modalIngVirya.value = ing.potency_virya || "";
    DOM.modalIngAyurveda.value = ing.ayurvedic_significance || "";
  } else {
    DOM.ingredientModalTitle.textContent = "🌿 Add New Ayurvedic Ingredient";
    DOM.modalIngId.value = "";
    DOM.modalIngNameEn.value = "";
    DOM.modalIngNameHi.value = "";
    DOM.modalIngNameMr.value = "";
    DOM.modalIngCategory.value = "Spices & Healing Herbs";
    DOM.modalIngCalories.value = "";
    DOM.modalIngZinc.value = "";
    DOM.modalIngIron.value = "";
    DOM.modalIngCalcium.value = "";
    DOM.modalIngProtein.value = "";
    DOM.modalIngFiber.value = "";
    DOM.modalIngMicro.value = "";
    DOM.modalIngDosha.value = "";
    DOM.modalIngRasa.value = "";
    DOM.modalIngVirya.value = "";
    DOM.modalIngAyurveda.value = "";
  }
  DOM.ingredientModal.classList.add("show");
  DOM.modalIngNameEn.focus();
}

function closeIngredientModal() {
  DOM.ingredientModal.classList.remove("show");
}

async function saveIngredientModal() {
  const nameEn = DOM.modalIngNameEn.value.trim();
  if (!nameEn) {
    alert("Please enter the English name for the ingredient.");
    DOM.modalIngNameEn.focus();
    return;
  }

  const ingId = DOM.modalIngId.value ? parseInt(DOM.modalIngId.value) : null;
  const payload = {
    name_en: nameEn,
    name_hi: DOM.modalIngNameHi.value.trim(),
    name_mr: DOM.modalIngNameMr.value.trim(),
    category: DOM.modalIngCategory.value,
    calories_per_100g: DOM.modalIngCalories.value.trim(),
    zinc: DOM.modalIngZinc.value.trim(),
    iron: DOM.modalIngIron.value.trim(),
    calcium: DOM.modalIngCalcium.value.trim(),
    protein: DOM.modalIngProtein.value.trim(),
    fiber: DOM.modalIngFiber.value.trim(),
    micronutrients: DOM.modalIngMicro.value.trim(),
    dosha_effect: DOM.modalIngDosha.value.trim(),
    taste_rasa: DOM.modalIngRasa.value.trim(),
    potency_virya: DOM.modalIngVirya.value.trim(),
    ayurvedic_significance: DOM.modalIngAyurveda.value.trim(),
  };

  const isUpdating = !!ingId;
  const url = isUpdating ? `/api/ingredients/${ingId}` : "/api/ingredients";
  const method = isUpdating ? "PUT" : "POST";

  try {
    const res = await fetch(url, {
      method: method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (res.ok) {
      closeIngredientModal();
      await loadPantryIngredients();
    } else {
      const errData = await res.json();
      alert("Failed to save ingredient: " + (errData.error || "Unknown error"));
    }
  } catch (err) {
    console.error("Error saving ingredient:", err);
    alert("Error saving ingredient: " + err.message);
  }
}

async function deleteIngredientFromPantry(id, name) {
  if (!confirm(`Are you sure you want to delete "${name}" from your pantry encyclopedia?`)) {
    return;
  }
  try {
    const res = await fetch(`/api/ingredients/${id}`, { method: "DELETE" });
    if (res.ok) {
      await loadPantryIngredients();
    } else {
      alert("Failed to delete ingredient.");
    }
  } catch (err) {
    console.error("Error deleting ingredient:", err);
    alert("Error deleting ingredient: " + err.message);
  }
}

// ------------------------------------------------------------------------------
// API & DATA OPERATIONS: RECIPES
// ------------------------------------------------------------------------------

async function loadRecipes() {
  try {
    const res = await fetch("/api/recipes");
    const data = await res.json();
    AppState.recipes = data.recipes || [];
    renderCatalog(AppState.recipes);
  } catch (err) {
    console.error("Failed to load recipes:", err);
  }
}

function filterCatalog() {
  const query = DOM.searchInput.value.toLowerCase().trim();
  const category = DOM.categoryFilter.value;

  const filtered = AppState.recipes.filter((r) => {
    const matchesQuery =
      !query ||
      (r.title && r.title.toLowerCase().includes(query)) ||
      (r.description && r.description.toLowerCase().includes(query)) ||
      (r.notes && r.notes.toLowerCase().includes(query)) ||
      (r.ayurvedic_note && r.ayurvedic_note.toLowerCase().includes(query));

    const matchesCat =
      !category || category === "all" || r.category === category;
    return matchesQuery && matchesCat;
  });

  renderCatalog(filtered);
}

function renderCatalog(recipes) {
  DOM.catalogGrid.innerHTML = "";
  DOM.catalogCount.textContent = `${recipes.length} Card${recipes.length === 1 ? "" : "s"}`;

  if (recipes.length === 0) {
    DOM.catalogGrid.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 3rem; color: #cbbaa5;">
        <p style="font-size: 1.2rem; margin-bottom: 0.5rem;">📜 No recipe cards found</p>
        <p style="font-size: 0.9rem; font-style: italic;">Try clearing filters or click "New Recipe Card" to create one!</p>
      </div>
    `;
    return;
  }

  recipes.forEach((recipe) => {
    const cardEl = document.createElement("div");
    cardEl.className = "catalog-card-item";
    const imgUrl = recipe.image_url || "/assets/placeholder_food.svg";

    cardEl.innerHTML = `
      <div class="catalog-thumb">
        <img src="${imgUrl}" alt="${escapeHtml(recipe.title)}" loading="lazy" />
        <span class="catalog-category-tag">${escapeHtml(recipe.category || "General")}</span>
      </div>
      <div class="catalog-details">
        <h3 class="catalog-title">${escapeHtml(recipe.title)}</h3>
        <p class="catalog-desc">${escapeHtml(recipe.description || "An authentic family heirloom recipe.")}</p>
        <div class="catalog-meta">
          <span class="catalog-meta-item">🍽️ ${recipe.servings || 4} Servings</span>
          ${recipe.yield_grams ? `<span class="catalog-meta-item">⚖️ ${escapeHtml(String(recipe.yield_grams))} g yield</span>` : ""}
          <span class="catalog-meta-item">⏱️ ${recipe.total_time || "30 mins"}</span>
          <span class="catalog-meta-item">📝 ${(recipe.ingredients || []).length} Ing.</span>
          ${recipe.calories ? `<span class="catalog-meta-item" style="color:var(--vintage-burgundy); font-weight:700;">⚡ ${escapeHtml(recipe.calories)}</span>` : ""}
          ${recipe.iron ? `<span class="catalog-meta-item" style="color:#6e2217;">🩸 Fe: ${escapeHtml(recipe.iron)}</span>` : ""}
          ${recipe.zinc ? `<span class="catalog-meta-item" style="color:#8f3426;">⚡ Zn: ${escapeHtml(recipe.zinc)}</span>` : ""}
        </div>
        ${recipe.ayurvedic_note ? `<div style="font-size:0.75rem; color:#2e4d2c; font-weight:600; margin-top:4px;">🌿 ${escapeHtml(recipe.ayurvedic_note)}</div>` : ""}
        <div class="catalog-card-actions">
          <button class="btn-rustic btn-view" data-id="${recipe.id}">🔍 View Card</button>
          <button class="btn-rustic btn-edit" data-id="${recipe.id}">✏️ Edit</button>
          <button class="btn-rustic btn-delete" data-id="${recipe.id}">🗑️</button>
        </div>
      </div>
    `;

    // Action clicks
    cardEl.querySelector(".btn-view").addEventListener("click", (e) => {
      e.stopPropagation();
      openRecipeInMaker(recipe.id, false);
    });

    cardEl.querySelector(".btn-edit").addEventListener("click", (e) => {
      e.stopPropagation();
      openRecipeInMaker(recipe.id, true);
    });

    cardEl.querySelector(".btn-delete").addEventListener("click", (e) => {
      e.stopPropagation();
      deleteRecipe(recipe.id, recipe.title);
    });

    // Whole card click opens view
    cardEl.addEventListener("click", () => openRecipeInMaker(recipe.id, false));

    DOM.catalogGrid.appendChild(cardEl);
  });
}

async function openRecipeInMaker(recipeId, editMode = false) {
  try {
    const res = await fetch(`/api/recipes/${recipeId}`);
    const data = await res.json();
    if (!data.recipe) {
      alert("Could not load recipe details.");
      return;
    }

    AppState.activeRecipe = data.recipe;
    AppState.isEditing = editMode;
    populateFormWithRecipe(data.recipe);
    switchView("maker");
  } catch (err) {
    console.error("Error loading recipe details:", err);
    alert("Error loading recipe details.");
  }
}

function createNewRecipe() {
  AppState.activeRecipe = {
    id: null,
    title: "Golden Turmeric Milk (Haldi Doodh)",
    category: "Healing Elixirs & Teas",
    servings: 2,
    yield_grams: 500,
    prep_time: "5 mins",
    cook_time: "10 mins",
    total_time: "15 mins",
    calories: "145 kcal",
    protein: "5g",
    carbs: "12g",
    fat: "8g",
    fiber: "1g",
    iron: "3.5 mg",
    zinc: "1.2 mg",
    ayurvedic_note: "Tridoshic | Boosts vital Ojas and immunity",
    image_url: "/assets/placeholder_food.svg",
    description: "Authentic Ayurvedic healing elixir crafted with spiced cow milk, golden turmeric, green cardamom, black pepper, and pure desi ghee.",
    notes: "Always add a pinch of freshly crushed black pepper to activate curcumin absorption.",
    ingredients: [
      { amount: "2", unit: "cups", name: "Whole Milk (Cow Doodh)", notes: "boiled fresh" },
      { amount: "1/2", unit: "tsp", name: "Turmeric (हल्दी / हळद)", notes: "pure aromatic powder" },
      { amount: "1/4", unit: "tsp", name: "Black Peppercorns (Kali Mirch)", notes: "freshly crushed" },
      { amount: "2", unit: "pods", name: "Cardamom (Green Elaichi)", notes: "lightly crushed" },
      { amount: "1/2", unit: "tsp", name: "Pure Desi Cow Ghee", notes: "stirred in hot" },
    ],
    instructions: [
      { instruction_text: "Pour milk into a heavy saucepan over medium heat with turmeric and crushed cardamom." },
      { instruction_text: "Simmer gently for 5 to 7 minutes to infuse botanical aromas." },
      { instruction_text: "Turn off heat, stir in pure desi ghee and a pinch of black pepper; strain and sip warm." },
    ],
  };
  AppState.isEditing = true;
  populateFormWithRecipe(AppState.activeRecipe);
}

function populateFormWithRecipe(recipe) {
  DOM.formRecipeId.value = recipe.id || "";
  DOM.formTitle.value = recipe.title || "";
  DOM.formCategory.value = recipe.category || "General";
  DOM.formServings.value = recipe.servings || 4;
  DOM.formYieldGrams.value = recipe.yield_grams || "";
  DOM.formPrepTime.value = recipe.prep_time || "15 mins";
  DOM.formCookTime.value = recipe.cook_time || "30 mins";
  DOM.formTotalTime.value = recipe.total_time || "45 mins";
  DOM.formCalories.value = recipe.calories || "";
  DOM.formProtein.value = recipe.protein || "";
  DOM.formCarbs.value = recipe.carbs || "";
  DOM.formFat.value = recipe.fat || "";
  DOM.formIron.value = recipe.iron || "";
  DOM.formZinc.value = recipe.zinc || "";
  DOM.formFiber.value = recipe.fiber || "";
  DOM.formAyurvedicNote.value = recipe.ayurvedic_note || "";
  DOM.formDescription.value = recipe.description || "";
  DOM.formNotes.value = recipe.notes || "";
  DOM.formImageUrl.value = recipe.image_url || "";

  // Populate Ingredients in Editor
  DOM.ingredientsEditorList.innerHTML = "";
  if (recipe.ingredients && recipe.ingredients.length > 0) {
    recipe.ingredients.forEach((ing) => addIngredientRow(ing));
  } else {
    addIngredientRow();
  }

  // Populate Steps in Editor
  DOM.stepsEditorList.innerHTML = "";
  if (recipe.instructions && recipe.instructions.length > 0) {
    recipe.instructions.forEach((step) => {
      const text = typeof step === "string" ? step : step.instruction_text;
      addStepRow(text);
    });
  } else {
    addStepRow();
  }

  // Sync with Live Card
  syncEntireCard();
}

// ------------------------------------------------------------------------------
// LIVE CARD SYNCHRONIZATION
// ------------------------------------------------------------------------------

function syncEntireCard() {
  syncTitle();
  syncCategory();
  syncServings();
  syncTimes();
  syncNutrients();
  syncMicroNutrients();
  syncPhoto();
  syncIngredientsToCard();
  syncStepsToCard();
}

function syncNutrients() {
  const cal = DOM.formCalories.value.trim();
  const pro = DOM.formProtein.value.trim();
  const carb = DOM.formCarbs.value.trim();
  const fat = DOM.formFat.value.trim();

  DOM.cardCalories.textContent = cal || "--";
  DOM.cardProtein.textContent = pro || "--";
  DOM.cardCarbs.textContent = carb || "--";
  DOM.cardFat.textContent = fat || "--";

  if (!cal && !pro && !carb && !fat) {
    DOM.cardNutrientsRow.style.display = "none";
  } else {
    DOM.cardNutrientsRow.style.display = "grid";
  }
}

function syncMicroNutrients() {
  const iron = DOM.formIron.value.trim();
  const zinc = DOM.formZinc.value.trim();
  const ayur = DOM.formAyurvedicNote.value.trim();

  let hasAny = false;

  if (iron) {
    DOM.cardIronVal.textContent = iron;
    DOM.cardIronPill.style.display = "inline-flex";
    hasAny = true;
  } else {
    DOM.cardIronPill.style.display = "none";
  }

  if (zinc) {
    DOM.cardZincVal.textContent = zinc;
    DOM.cardZincPill.style.display = "inline-flex";
    hasAny = true;
  } else {
    DOM.cardZincPill.style.display = "none";
  }

  if (ayur) {
    DOM.cardAyurText.textContent = ayur;
    DOM.cardAyurvedicBadge.style.display = "inline-flex";
    hasAny = true;
  } else {
    DOM.cardAyurvedicBadge.style.display = "none";
  }

  DOM.cardMicroNutrientsRow.style.display = hasAny ? "flex" : "none";
}

function syncTitle() {
  const title = DOM.formTitle.value.trim() || "Untitled Recipe";
  DOM.cardTitle.textContent = title;
}

function syncCategory() {
  DOM.cardCategoryBadge.textContent = DOM.formCategory.value;
}

function syncServings() {
  DOM.cardServings.textContent = DOM.formServings.value || 4;
  const yieldGrams = DOM.formYieldGrams.value.trim();
  DOM.cardYieldGrams.textContent = yieldGrams ? `${yieldGrams} g` : "—";
}

function syncTimes() {
  DOM.cardPrepTime.textContent = DOM.formPrepTime.value || "15 mins";
  DOM.cardTotalTime.textContent = DOM.formTotalTime.value || "45 mins";
}

function syncPhoto() {
  const url = DOM.formImageUrl.value.trim() || "/assets/placeholder_food.svg";
  DOM.cardPhotoImg.src = url;
}

function syncIngredientsToCard() {
  DOM.cardIngredientsList.innerHTML = "";
  const rows = DOM.ingredientsEditorList.querySelectorAll(".ingredient-input-row");

  rows.forEach((row) => {
    const amount = row.querySelector(".ing-amt").value.trim();
    const unit = row.querySelector(".ing-unit").value.trim();
    const name = row.querySelector(".ing-name-input").value.trim();
    const notes = row.querySelector(".ing-notes-input")
      ? row.querySelector(".ing-notes-input").value.trim()
      : "";

    if (name) {
      const ayurName = row.dataset.ayurName || "";
      const li = document.createElement("div");
      li.className = "ingredient-item";

      const amtUnitStr = [amount, unit].filter(Boolean).join(" ");
      li.innerHTML = `
        <span class="ing-bullet">❦</span>
        ${amtUnitStr ? `<span class="ing-amount-unit">${escapeHtml(amtUnitStr)}</span>` : ""}
        <span class="ing-name">${escapeHtml(name)}</span>
        ${ayurName ? `<span class="ing-ayur-name">(${escapeHtml(ayurName)})</span>` : ""}
        ${notes ? `<span class="ing-notes">(${escapeHtml(notes)})</span>` : ""}
      `;
      DOM.cardIngredientsList.appendChild(li);
    }
  });

  if (DOM.cardIngredientsList.children.length === 0) {
    DOM.cardIngredientsList.innerHTML = `<div style="font-size: 0.75rem; color: #999; font-style: italic;">No ingredients added yet.</div>`;
  }
}

function syncStepsToCard() {
  DOM.cardMethodSteps.innerHTML = "";
  const rows = DOM.stepsEditorList.querySelectorAll(".step-input-row");
  let stepNumber = 1;

  rows.forEach((row) => {
    const text = row.querySelector(".step-textarea").value.trim();
    if (text) {
      const stepDiv = document.createElement("div");
      stepDiv.className = "method-step-item";
      stepDiv.innerHTML = `
        <span class="step-badge">${stepNumber}</span>
        <span class="step-text">${escapeHtml(text)}</span>
      `;
      DOM.cardMethodSteps.appendChild(stepDiv);
      stepNumber++;
    }
  });

  if (DOM.cardMethodSteps.children.length === 0) {
    DOM.cardMethodSteps.innerHTML = `<div style="font-size: 0.75rem; color: #999; font-style: italic;">No instructions added yet.</div>`;
  }
}

// ------------------------------------------------------------------------------
// INGREDIENTS & STEPS ROW BUILDERS (WITH TRILINGUAL AUTOCOMPLETE)
// ------------------------------------------------------------------------------

function addIngredientRow(data = {}) {
  const row = document.createElement("div");
  row.className = "ingredient-input-row";

  row.innerHTML = `
    <input type="text" class="rustic-input ing-amt" placeholder="Amt" value="${escapeHtml(data.amount || "")}" />
    <input type="text" class="rustic-input ing-unit" placeholder="Unit" value="${escapeHtml(data.unit || "")}" />
    <div class="autocomplete-container">
      <input type="text" class="rustic-input ing-name-input" placeholder="Ingredient in English, हिंदी, or मराठी..." value="${escapeHtml(data.name || "")}" autocomplete="off" />
      <div class="autocomplete-dropdown"></div>
    </div>
    <button type="button" class="btn-icon-del" title="Remove ingredient">✕</button>
  `;

  const amtInput = row.querySelector(".ing-amt");
  const unitInput = row.querySelector(".ing-unit");
  const nameInput = row.querySelector(".ing-name-input");
  const dropdown = row.querySelector(".autocomplete-dropdown");
  const btnDel = row.querySelector(".btn-icon-del");

  // Autocomplete setup
  nameInput.addEventListener("input", (e) => {
    handleIngredientAutocomplete(e.target.value, dropdown, nameInput);
    syncIngredientsToCard();
  });

  nameInput.addEventListener("focus", (e) => {
    if (e.target.value) {
      handleIngredientAutocomplete(e.target.value, dropdown, nameInput);
    }
  });

  // Close dropdown on click outside
  document.addEventListener("click", (e) => {
    if (!row.contains(e.target)) {
      dropdown.classList.remove("show");
    }
  });

  amtInput.addEventListener("input", syncIngredientsToCard);
  unitInput.addEventListener("input", syncIngredientsToCard);

  btnDel.addEventListener("click", () => {
    row.remove();
    syncIngredientsToCard();
  });

  DOM.ingredientsEditorList.appendChild(row);
  syncIngredientsToCard();
}

function handleIngredientAutocomplete(query, dropdown, inputEl) {
  const q = query.toLowerCase().trim();
  if (!q) {
    dropdown.classList.remove("show");
    return;
  }

  const matches = AppState.ingredients
    .filter((item) => {
      return (
        (item.name_en && item.name_en.toLowerCase().includes(q)) ||
        (item.name_hi && item.name_hi.toLowerCase().includes(q)) ||
        (item.name_mr && item.name_mr.toLowerCase().includes(q))
      );
    })
    .slice(0, 8);

  if (matches.length === 0) {
    dropdown.classList.remove("show");
    return;
  }

  dropdown.innerHTML = "";
  matches.forEach((item) => {
    const opt = document.createElement("div");
    opt.className = "autocomplete-item";

    const hiText = item.name_hi ? ` / ${item.name_hi}` : "";
    const mrText = item.name_mr ? ` (${item.name_mr})` : "";
    const zincIron = [
      item.iron ? `Fe: ${item.iron}` : null,
      item.zinc ? `Zn: ${item.zinc}` : null
    ].filter(Boolean).join(" | ");

    opt.innerHTML = `
      <div>
        <span style="font-weight:700;">${escapeHtml(item.name_en)}${escapeHtml(hiText)}${escapeHtml(mrText)}</span>
        ${zincIron ? `<span style="font-size:0.68rem; color:#8f3426; margin-left:6px;">[${escapeHtml(zincIron)}]</span>` : ""}
      </div>
      <span class="item-cat">${escapeHtml(item.category)}</span>
    `;

    opt.addEventListener("click", () => {
      let selectedText = item.name_en;
      if (item.name_hi) selectedText += ` (${item.name_hi})`;
      inputEl.value = selectedText;
      dropdown.classList.remove("show");
      syncIngredientsToCard();

      // Auto-fill nutrient hints if currently blank in recipe
      if (!DOM.formIron.value && item.iron) {
        DOM.formIron.value = item.iron;
        syncMicroNutrients();
      }
      if (!DOM.formZinc.value && item.zinc) {
        DOM.formZinc.value = item.zinc;
        syncMicroNutrients();
      }
      if (!DOM.formAyurvedicNote.value && item.dosha_effect) {
        DOM.formAyurvedicNote.value = item.dosha_effect;
        syncMicroNutrients();
      }
    });

    dropdown.appendChild(opt);
  });

  dropdown.classList.add("show");
}

function addStepRow(text = "") {
  const row = document.createElement("div");
  row.className = "step-input-row";

  row.innerHTML = `
    <span style="color:#d8c2a3; font-weight:bold; padding-top:6px; font-size:0.85rem;">•</span>
    <textarea class="rustic-input step-textarea" rows="2" placeholder="Step instructions...">${escapeHtml(text)}</textarea>
    <button type="button" class="btn-icon-del" title="Remove step">✕</button>
  `;

  const textarea = row.querySelector(".step-textarea");
  const btnDel = row.querySelector(".btn-icon-del");

  textarea.addEventListener("input", syncStepsToCard);
  btnDel.addEventListener("click", () => {
    row.remove();
    syncStepsToCard();
  });

  DOM.stepsEditorList.appendChild(row);
  syncStepsToCard();
}

// ------------------------------------------------------------------------------
// IMAGE UPLOADING
// ------------------------------------------------------------------------------

async function handleImageUpload(e) {
  const file = e.target.files[0];
  if (!file) return;
  await uploadImageFile(file);
}

async function uploadImageFile(file) {
  if (!file.type.startsWith("image/")) {
    alert("Please select a valid image file.");
    return;
  }

  // Read as base64 data URI
  const reader = new FileReader();
  reader.onload = async (event) => {
    const dataUri = event.target.result;

    // Show instant local preview on the card
    DOM.formImageUrl.value = dataUri;
    DOM.cardPhotoImg.src = dataUri;

    // Upload to server
    try {
      const res = await fetch("/api/upload", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          filename: file.name,
          data: dataUri,
        }),
      });
      const data = await res.json();
      if (data.url) {
        DOM.formImageUrl.value = data.url;
        DOM.cardPhotoImg.src = data.url;
      }
    } catch (err) {
      console.warn("Upload failed, retaining local base64 preview:", err);
    }
  };
  reader.readAsDataURL(file);
}

// ------------------------------------------------------------------------------
// SAVE & DELETE OPERATIONS: RECIPES
// ------------------------------------------------------------------------------

function collectFormData() {
  const recipeId = DOM.formRecipeId.value ? parseInt(DOM.formRecipeId.value) : null;

  const ingredients = [];
  const ingRows = DOM.ingredientsEditorList.querySelectorAll(".ingredient-input-row");
  ingRows.forEach((row) => {
    const name = row.querySelector(".ing-name-input").value.trim();
    if (name) {
      ingredients.push({
        amount: row.querySelector(".ing-amt").value.trim(),
        unit: row.querySelector(".ing-unit").value.trim(),
        name: name,
        notes: "",
      });
    }
  });

  const instructions = [];
  const stepRows = DOM.stepsEditorList.querySelectorAll(".step-input-row");
  stepRows.forEach((row) => {
    const text = row.querySelector(".step-textarea").value.trim();
    if (text) {
      instructions.push({ instruction_text: text });
    }
  });

  return {
    id: recipeId,
    title: DOM.formTitle.value.trim() || "Untitled Recipe",
    category: DOM.formCategory.value,
    servings: parseInt(DOM.formServings.value) || 4,
    yield_grams: parseInt(DOM.formYieldGrams.value) || 0,
    prep_time: DOM.formPrepTime.value.trim() || "15 mins",
    cook_time: DOM.formCookTime.value.trim() || "30 mins",
    total_time: DOM.formTotalTime.value.trim() || "45 mins",
    calories: DOM.formCalories.value.trim(),
    protein: DOM.formProtein.value.trim(),
    carbs: DOM.formCarbs.value.trim(),
    fat: DOM.formFat.value.trim(),
    iron: DOM.formIron.value.trim(),
    zinc: DOM.formZinc.value.trim(),
    fiber: DOM.formFiber.value.trim(),
    ayurvedic_note: DOM.formAyurvedicNote.value.trim(),
    description: DOM.formDescription.value.trim(),
    notes: DOM.formNotes.value.trim(),
    image_url: DOM.formImageUrl.value.trim() || "/assets/placeholder_food.svg",
    ingredients: ingredients,
    instructions: instructions,
  };
}

async function saveRecipe() {
  const data = collectFormData();
  if (!data.title || data.title === "Untitled Recipe") {
    alert("Please provide a recipe title before saving.");
    DOM.formTitle.focus();
    return;
  }

  const isUpdating = !!data.id;
  const url = isUpdating ? `/api/recipes/${data.id}` : "/api/recipes";
  const method = isUpdating ? "PUT" : "POST";

  DOM.btnSaveRecipe.disabled = true;
  DOM.btnSaveRecipe.textContent = "Saving...";

  try {
    const res = await fetch(url, {
      method: method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    const result = await res.json();
    if (res.ok && result.recipe) {
      DOM.formRecipeId.value = result.recipe.id;
      AppState.activeRecipe = result.recipe;
      alert(`✨ Recipe "${result.recipe.title}" saved successfully to your recipe drawer!`);
      await loadRecipes();
    } else {
      alert("Save failed: " + (result.error || "Unknown server error"));
    }
  } catch (err) {
    console.error("Error saving recipe:", err);
    alert("Error saving recipe: " + err.message);
  } finally {
    DOM.btnSaveRecipe.disabled = false;
    DOM.btnSaveRecipe.textContent = "💾 Save Recipe";
  }
}

async function deleteRecipe(id, title) {
  if (!confirm(`Are you sure you want to delete "${title}" from your recipe box?`)) {
    return;
  }

  try {
    const res = await fetch(`/api/recipes/${id}`, { method: "DELETE" });
    if (res.ok) {
      await loadRecipes();
      if (AppState.activeRecipe && AppState.activeRecipe.id === id) {
        createNewRecipe();
      }
    } else {
      alert("Failed to delete recipe.");
    }
  } catch (err) {
    console.error("Error deleting recipe:", err);
    alert("Error deleting recipe: " + err.message);
  }
}

// ------------------------------------------------------------------------------
// UTILITY HELPERS
// ------------------------------------------------------------------------------

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function debounce(func, wait) {
  let timeout;
  return function (...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}
