/**
 * Exporter utility for Rustic Recipe Card Maker
 * - High-resolution JPG image exporter (300 DPI index card print ready)
 * - Print handling for 3x5", 4x6", 5x7", and Letter paper with cutting guidelines
 */

const CardExporter = {
  /**
   * Export the recipe card element as a JPG image
   * @param {HTMLElement} cardEl - The .recipe-index-card DOM element
   * @param {Object} recipeData - Recipe metadata for filename and canvas fallback
   */
  async exportToJpg(cardEl, recipeData = {}) {
    if (!cardEl) {
      alert("No recipe card found to export.");
      return;
    }

    const safeTitle = (recipeData.title || "recipe")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/(^-|-$)/g, "");
    const filename = `recipe-${safeTitle || "card"}.jpg`;

    // Show export progress indicator on button if present
    const exportBtn = document.getElementById("btnExportJpg");
    const originalText = exportBtn ? exportBtn.innerHTML : "";
    if (exportBtn) {
      exportBtn.innerHTML = "⏳ Rendering JPG...";
      exportBtn.disabled = true;
    }

    try {
      // Determine card dimensions (aim for 300 DPI high resolution)
      const rect = cardEl.getBoundingClientRect();
      const scaleFactor = 2.5; // High-res scale factor
      const width = Math.round(rect.width * scaleFactor);
      const height = Math.round(rect.height * scaleFactor);

      // Try ForeignObject rendering first for exact CSS fidelity
      const dataUrl = await this.renderCardToDataUrl(cardEl, width, height, recipeData);

      // Trigger instant download
      const link = document.createElement("a");
      link.download = filename;
      link.href = dataUrl;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      console.warn("ForeignObject rendering failed, falling back to direct Canvas drawing:", err);
      try {
        const fallbackUrl = await this.drawDirectCanvas(cardEl, recipeData);
        const link = document.createElement("a");
        link.download = filename;
        link.href = fallbackUrl;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      } catch (canvasErr) {
        console.error("Direct canvas export failed:", canvasErr);
        alert("Export failed: " + canvasErr.message);
      }
    } finally {
      if (exportBtn) {
        exportBtn.innerHTML = originalText;
        exportBtn.disabled = false;
      }
    }
  },

  /**
   * Render card using SVG ForeignObject technique into Canvas
   */
  async renderCardToDataUrl(cardEl, targetWidth, targetHeight, recipeData) {
    const clone = cardEl.cloneNode(true);

    // Apply inline style adjustments to ensure self-contained render
    clone.style.transform = "none";
    clone.style.margin = "0";
    clone.style.position = "static";

    // Remove interactive overlays
    const overlays = clone.querySelectorAll(".photo-overlay-btn");
    overlays.forEach((el) => el.remove());

    // Serialize DOM to XHTML
    const serializer = new XMLSerializer();
    const xhtml = serializer.serializeToString(clone);

    // Embed all stylesheet styles directly
    const cssRules = [];
    for (const sheet of document.styleSheets) {
      try {
        for (const rule of sheet.cssRules) {
          cssRules.push(rule.cssText);
        }
      } catch (e) {
        // Cross-origin CSS protection bypass if any
      }
    }

    const svgXml = `
      <svg xmlns="http://www.w3.org/2000/svg" width="${targetWidth}" height="${targetHeight}">
        <style>
          ${cssRules.join("\n")}
          .recipe-index-card { width: 100% !important; height: 100% !important; box-shadow: none !important; }
        </style>
        <foreignObject width="100%" height="100%">
          <div xmlns="http://www.w3.org/1999/xhtml" style="width:100%;height:100%;">
            ${xhtml}
          </div>
        </foreignObject>
      </svg>
    `;

    return new Promise((resolve, reject) => {
      const img = new Image();
      const svgBlob = new Blob([svgXml], { type: "image/svg+xml;charset=utf-8" });
      const url = URL.createObjectURL(svgBlob);

      img.onload = () => {
        const canvas = document.createElement("canvas");
        canvas.width = targetWidth;
        canvas.height = targetHeight;
        const ctx = canvas.getContext("2d");

        // Fill background color
        ctx.fillStyle = "#f7f2e6";
        ctx.fillRect(0, 0, targetWidth, targetHeight);

        // Draw rendered SVG
        ctx.drawImage(img, 0, 0, targetWidth, targetHeight);
        URL.revokeObjectURL(url);

        try {
          const jpgDataUrl = canvas.toDataURL("image/jpeg", 0.95);
          resolve(jpgDataUrl);
        } catch (canvasErr) {
          reject(canvasErr);
        }
      };

      img.onerror = (e) => {
        URL.revokeObjectURL(url);
        reject(new Error("SVG image load failed"));
      };

      img.src = url;
    });
  },

  /**
   * Direct high-fidelity Canvas 2D fallback renderer (1500x900 for 3x5 at 300 DPI)
   */
  async drawDirectCanvas(cardEl, data) {
    const canvas = document.createElement("canvas");
    canvas.width = 1500;
    canvas.height = 900;
    const ctx = canvas.getContext("2d");

    // Parchment gradient background
    const bgGrad = ctx.createRadialGradient(750, 450, 50, 750, 450, 800);
    bgGrad.addColorStop(0, "#fdfaf3");
    bgGrad.addColorStop(0.7, "#f5ecd8");
    bgGrad.addColorStop(1, "#dfc8a5");
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, 1500, 900);

    // Outer and inner antique borders
    ctx.strokeStyle = "#8c6f50";
    ctx.lineWidth = 4;
    ctx.strokeRect(20, 20, 1460, 860);

    ctx.strokeStyle = "#c7964b";
    ctx.lineWidth = 2;
    ctx.strokeRect(30, 30, 1440, 840);

    // Decorative corner flourishes
    ctx.fillStyle = "#c7964b";
    ctx.font = "32px serif";
    ctx.fillText("✦", 40, 65);
    ctx.fillText("✦", 1435, 65);
    ctx.fillText("✦", 40, 850);
    ctx.fillText("✦", 1435, 850);

    // Dividing column line
    const colSplit = 600;
    ctx.strokeStyle = "#bb9f7c";
    ctx.lineWidth = 2;
    ctx.setLineDash([6, 6]);
    ctx.beginPath();
    ctx.moveTo(colSplit, 40);
    ctx.lineTo(colSplit, 860);
    ctx.stroke();
    ctx.setLineDash([]);

    // --- LEFT COLUMN ---
    // Title
    ctx.fillStyle = "#241913";
    ctx.font = "bold 38px Georgia, serif";
    const title = data.title || "Recipe Title";
    ctx.fillText(title.substring(0, 35), 55, 95);

    // Category
    if (data.category) {
      ctx.fillStyle = "#8f3426";
      ctx.font = "bold 18px Georgia, serif";
      ctx.fillText(data.category.toUpperCase(), 55, 125);
    }

    // Photo placeholder / image
    const photoBoxY = 145;
    const photoBoxH = 460;
    ctx.fillStyle = "#eeddc3";
    ctx.fillRect(55, photoBoxY, 500, photoBoxH);
    ctx.strokeStyle = "#bb9f7c";
    ctx.strokeRect(55, photoBoxY, 500, photoBoxH);

    // Try drawing image if loaded
    const imgEl = cardEl.querySelector(".card-photo-img");
    if (imgEl && imgEl.complete && imgEl.naturalWidth > 0) {
      try {
        ctx.drawImage(imgEl, 55, photoBoxY, 500, photoBoxH);
      } catch (e) {
        ctx.fillStyle = "#5e483b";
        ctx.font = "20px Georgia, serif";
        ctx.fillText("Photo: " + title, 160, photoBoxY + 230);
      }
    } else {
      ctx.fillStyle = "#5e483b";
      ctx.font = "20px Georgia, serif";
      ctx.fillText("Rustic Recipe Kitchen", 180, photoBoxY + 230);
    }

    // Meta row (Servings, Prep, Total)
    const metaY = 625;
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(55, metaY, 500, 100);
    ctx.strokeStyle = "#bb9f7c";
    ctx.strokeRect(55, metaY, 500, 100);

    ctx.fillStyle = "#5e483b";
    ctx.font = "13px Georgia, serif";
    ctx.fillText("SERVINGS", 90, metaY + 30);
    ctx.fillText("PREP TIME", 250, metaY + 30);
    ctx.fillText("TOTAL TIME", 410, metaY + 30);

    ctx.fillStyle = "#241913";
    ctx.font = "bold 20px Georgia, serif";
    ctx.fillText(String(data.servings || 4), 105, metaY + 68);
    ctx.fillText(String(data.prep_time || "15 mins"), 250, metaY + 68);
    ctx.fillText(String(data.total_time || "45 mins"), 415, metaY + 68);

    // Nutrients row (Calories, Protein, Carbs, Fat)
    const nutY = 735;
    ctx.fillStyle = "#fdfaf3";
    ctx.fillRect(55, nutY, 500, 75);
    ctx.strokeStyle = "#bb9f7c";
    ctx.strokeRect(55, nutY, 500, 75);

    ctx.fillStyle = "#8f3426";
    ctx.font = "bold 11px Georgia, serif";
    ctx.fillText("⚡ CALORIES", 70, nutY + 24);
    ctx.fillText("🥩 PROTEIN", 195, nutY + 24);
    ctx.fillText("🌾 CARBS", 320, nutY + 24);
    ctx.fillText("🧈 FAT", 445, nutY + 24);

    ctx.fillStyle = "#241913";
    ctx.font = "bold 16px Georgia, serif";
    ctx.fillText(data.calories || "--", 75, nutY + 54);
    ctx.fillText(data.protein || "--", 205, nutY + 54);
    ctx.fillText(data.carbs || "--", 330, nutY + 54);
    ctx.fillText(data.fat || "--", 450, nutY + 54);

    // Micronutrients & Ayurvedic Ribbon
    const microParts = [
      data.iron ? `Fe: ${data.iron}` : null,
      data.zinc ? `Zn: ${data.zinc}` : null,
      data.ayurvedic_note ? `🌿 ${data.ayurvedic_note}` : null
    ].filter(Boolean).join("  |  ");

    if (microParts) {
      ctx.fillStyle = "#2e4d2c";
      ctx.font = "italic 13px Georgia, serif";
      ctx.fillText(microParts.substring(0, 52), 55, 835);
    }

    // --- RIGHT COLUMN ---
    // Top: Ingredients header
    ctx.fillStyle = "#8f3426";
    ctx.font = "bold 22px Georgia, serif";
    ctx.fillText("INGREDIENTS", 640, 85);
    ctx.strokeStyle = "#bb9f7c";
    ctx.beginPath();
    ctx.moveTo(800, 78);
    ctx.lineTo(1440, 78);
    ctx.stroke();

    // Ingredients list
    ctx.fillStyle = "#382921";
    ctx.font = "19px Georgia, serif";
    let ingY = 120;
    const ingredients = data.ingredients || [];
    for (let i = 0; i < Math.min(ingredients.length, 9); i++) {
      const ing = ingredients[i];
      const amtUnit = [ing.amount, ing.unit].filter(Boolean).join(" ");
      const name = ing.name || "";
      const text = `• ${amtUnit ? amtUnit + " " : ""}${name}`;
      ctx.fillText(text.substring(0, 55), 640, ingY);
      ingY += 32;
    }

    // Bottom: Method / Instructions Header
    const methodHeaderY = Math.max(ingY + 25, 460);
    ctx.fillStyle = "#8f3426";
    ctx.font = "bold 22px Georgia, serif";
    ctx.fillText("METHOD & DIRECTIONS", 640, methodHeaderY);
    ctx.beginPath();
    ctx.moveTo(920, methodHeaderY - 7);
    ctx.lineTo(1440, methodHeaderY - 7);
    ctx.stroke();

    // Method steps
    ctx.fillStyle = "#382921";
    ctx.font = "18px Georgia, serif";
    let stepY = methodHeaderY + 40;
    const instructions = data.instructions || [];
    for (let i = 0; i < Math.min(instructions.length, 6); i++) {
      const inst = instructions[i];
      const text = typeof inst === "string" ? inst : inst.instruction_text || "";
      ctx.fillStyle = "#8f3426";
      ctx.fillText(`${i + 1}.`, 640, stepY);
      ctx.fillStyle = "#382921";
      ctx.fillText(text.substring(0, 65), 670, stepY);
      stepY += 32;
    }

    return canvas.toDataURL("image/jpeg", 0.95);
  },

  /**
   * Trigger native browser print dialog configured for card sizes
   * @param {string} mode - 'direct-3x5', 'direct-4x6', or 'letter-trim-marks'
   */
  printCard(mode = "direct-3x5") {
    // Remove previous print classes
    document.body.classList.remove(
      "print-index-card-direct",
      "print-with-trim-marks"
    );

    if (mode === "letter-trim-marks") {
      document.body.classList.add("print-with-trim-marks");
    } else {
      document.body.classList.add("print-index-card-direct");
    }

    window.print();
  }
};

window.CardExporter = CardExporter;
