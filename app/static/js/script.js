// --- Version depuis le footer (incrustée côté serveur) ---
const APP_VERSION = document.getElementById("versionInfo")?.textContent.split(": ")[1] || "";

// Utilitaire: normalise "2025/2026" -> "2025-2026"
function normalizeSeason(s) {
  return (s || "").replace("/", "-");
}

// --- Week-end courant (Samedi/Dimanche) ---
function getWeekendDates() {
  const now = new Date();
  const day = now.getDay(); // 0=Dim, 1=Lun, ..., 6=Sam
  const monday = new Date(now);
  monday.setDate(now.getDate() - ((day + 6) % 7));
  const saturday = new Date(monday);
  saturday.setDate(monday.getDate() + 5);
  const sunday = new Date(monday);
  sunday.setDate(monday.getDate() + 6);
  const fmt = d => d.toISOString().slice(0, 10);
  return { saturday: fmt(saturday), sunday: fmt(sunday) };
}

// --- Sync date_end sur le lendemain de date_start ---
function syncEndToNextDay(opts = { force: false }) {
  const start = document.getElementById("date_start");
  const end   = document.getElementById("date_end");
  if (!start || !end || !start.value) return;

  // Empêche une fin avant le début
  end.min = start.value;

  // Calcule le lendemain (robuste fuseau)
  let next;
  if (start.valueAsDate) {
    next = new Date(start.valueAsDate.getTime());
    next.setDate(next.getDate() + 1);
    if (opts.force || !end.value || end.value < start.value) {
      end.valueAsDate = next;
    }
  } else {
    const [y, m, d] = start.value.split("-").map(Number);
    next = new Date(y, m - 1, d);
    next.setDate(next.getDate() + 1);
    const iso = new Date(next.getTime() - next.getTimezoneOffset() * 60000)
      .toISOString().slice(0, 10);
    if (opts.force || !end.value || end.value < start.value) {
      end.value = iso;
    }
  }
}

// --- Chargement des templates ---
async function loadTemplates() {
  const sel = document.getElementById("template");

  sel.innerHTML = "";
  const loadingOpt = document.createElement("option");
  loadingOpt.text = "Chargement des templates…";
  loadingOpt.disabled = true;
  loadingOpt.selected = true;
  sel.add(loadingOpt);

  try {
    const resp = await fetch("/templates");
    if (!resp.ok) throw new Error("HTTP " + resp.status);
    const data = await resp.json();

    sel.innerHTML = "";

    const defaultOpt = document.createElement("option");
    defaultOpt.value = "";
    defaultOpt.text = `Par défaut (${data.default})`;
    sel.add(defaultOpt);

    // data.templates = { name: display_name, ... }
    Object.entries(data.templates).forEach(([name, description]) => {
      const opt = document.createElement("option");
      opt.value = name;
      opt.text = description;
      sel.add(opt);
    });
  } catch (e) {
    console.error("Erreur templates:", e);
    sel.innerHTML = "";
    const errOpt = document.createElement("option");
    errOpt.text = "Erreur de chargement des templates";
    errOpt.disabled = true;
    sel.add(errOpt);
  }
}

// --- Chargement des catégories ---
async function loadCategoriesForSeason() {
  const saisonRaw = document.getElementById("saison")?.value || "";
  const saison = normalizeSeason(saisonRaw);
  const sel = document.getElementById("categories");

  sel.innerHTML = "";
  const loadingOpt = document.createElement("option");
  loadingOpt.text = "Chargement des catégories…";
  loadingOpt.disabled = true;
  loadingOpt.selected = true;
  sel.add(loadingOpt);

  try {
    const resp = await fetch("/categories?saison=" + encodeURIComponent(saison));
    if (!resp.ok) throw new Error("HTTP " + resp.status);
    const data = await resp.json();

    sel.innerHTML = "";

    // Group by info.type using <optgroup>
    const groups = {};
    Object.entries(data).forEach(([code, info]) => {
      const groupKey = info.type || "Autres";
      if (!groups[groupKey]) groups[groupKey] = [];
      groups[groupKey].push({ code, info });
    });

    Object.entries(groups).forEach(([groupKey, items]) => {
      const grp = document.createElement("optgroup");
      grp.label = groupKey;
      items.forEach(({ code, info }) => {
        const opt = document.createElement("option");
        opt.value = code;
        const label = info.label || code;
        const genre = info.genre ? ` ${info.genre}` : "";
        opt.text = `[${label}]${genre}`;
        grp.appendChild(opt);
      });
      sel.add(grp);
    });

    // Sélectionne tout par défaut si rien n'est coché
    if (sel.options.length && !Array.from(sel.options).some(o => o.selected)) {
      Array.from(sel.options).forEach(o => (o.selected = true));
    }
  } catch (e) {
    console.error("Erreur catégories:", e);
    sel.innerHTML = "";
    const errOpt = document.createElement("option");
    errOpt.text = "Erreur de chargement des catégories";
    errOpt.disabled = true;
    sel.add(errOpt);
  }
}

// --- Status message ---
const statusMsg = document.getElementById("statusMsg");

function showStatus(msg, type = "info", autohideMs = 3000) {
  if (!statusMsg) return;
  statusMsg.className = "small";
  if (type === "ok")    statusMsg.classList.add("text-success");
  else if (type === "error") statusMsg.classList.add("text-danger");
  else                  statusMsg.classList.add("text-muted");
  statusMsg.textContent = msg;
  statusMsg.classList.remove("d-none");

  if (type !== "error" && autohideMs > 0) {
    clearTimeout(statusMsg._t);
    statusMsg._t = setTimeout(() => {
      statusMsg.classList.add("d-none");
    }, autohideMs);
  }
}

// --- Refresh config button ---
const refreshConfigBtn = document.getElementById("refreshConfigBtn");

function setRefreshBusy(busy) {
  if (!refreshConfigBtn) return;
  refreshConfigBtn.disabled = busy;
  refreshConfigBtn.innerHTML = busy
    ? '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>'
    : '<i class="bi bi-arrow-clockwise"></i>';
}

refreshConfigBtn?.addEventListener("click", async () => {
  if (refreshConfigBtn.disabled) return;
  try {
    setRefreshBusy(true);
    showStatus("Mise à jour…", "info", 0);
    const resp = await fetch("/update-config", { method: "POST" });
    const data = await resp.json();
    showStatus(data.message || "Configuration mise à jour.", "ok", 2500);
    await loadCategoriesForSeason();
  } catch (err) {
    showStatus("Échec de la mise à jour : " + err, "error", 0);
  } finally {
    setRefreshBusy(false);
  }
});

// --- Clear cache button ---
const clearCacheBtn = document.getElementById("clearCacheBtn");

function setCacheBusy(busy) {
  if (!clearCacheBtn) return;
  clearCacheBtn.disabled = busy;
  clearCacheBtn.innerHTML = busy
    ? '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>'
    : '<i class="bi bi-trash3"></i>';
}

clearCacheBtn?.addEventListener("click", async () => {
  if (clearCacheBtn.disabled) return;
  try {
    setCacheBusy(true);
    showStatus("Nettoyage du cache…", "info", 0);
    const resp = await fetch("/cache/clear", { method: "POST" });
    const data = await resp.json();
    const msg = data.deleted_files !== undefined
      ? `Cache vidé (${data.deleted_files} fichier(s) supprimé(s))`
      : data.message || "Cache vidé.";
    showStatus(msg, "ok", 2500);
  } catch (err) {
    showStatus("Échec du nettoyage : " + err, "error", 0);
  } finally {
    setCacheBusy(false);
  }
});

// --- Soumission du formulaire ---
async function submitForm(e) {
  e.preventDefault();

  const loadingEl    = document.getElementById("loading");
  const generateLabel = document.getElementById("generateLabel");
  const resultImg    = document.getElementById("resultImg");
  const emptyState   = document.getElementById("emptyState");
  const imageActions = document.getElementById("imageActions");

  loadingEl.classList.remove("d-none");
  generateLabel.classList.add("d-none");
  resultImg.classList.add("d-none");
  if (emptyState) emptyState.classList.remove("d-none");
  if (imageActions) imageActions.classList.add("d-none");

  const saisonRaw = document.getElementById("saison").value;
  const saison    = normalizeSeason(saisonRaw);
  const title     = document.getElementById("title").value;
  const format    = document.querySelector('input[name="format"]:checked').value;
  const template  = document.getElementById("template").value;
  const cats      = Array.from(document.getElementById("categories").selectedOptions).map(opt => opt.value);
  const date_start = document.getElementById("date_start").value;
  const date_end   = document.getElementById("date_end").value;
  const mode       = document.getElementById("mode").value;

  let url = "/image?mode=" + encodeURIComponent(mode);
  if (cats.length)  url += "&" + cats.map(c => "categories=" + encodeURIComponent(c)).join("&");
  if (saison)       url += "&saison=" + encodeURIComponent(saison);
  if (title)        url += "&title=" + encodeURIComponent(title);
  if (format)       url += "&format=" + encodeURIComponent(format);
  if (template)     url += "&template=" + encodeURIComponent(template);
  if (date_start)   url += "&date_start=" + encodeURIComponent(date_start);
  if (date_end)     url += "&date_end=" + encodeURIComponent(date_end);

  try {
    const r = await fetch(url);
    if (!r.ok) throw new Error("HTTP " + r.status);
    const blob   = await r.blob();
    const imgUrl = URL.createObjectURL(blob);
    resultImg.src = imgUrl;
    resultImg.classList.remove("d-none");
    if (emptyState) emptyState.classList.add("d-none");
  } catch (err) {
    console.error("Erreur génération image:", err);
    alert("Erreur lors de la génération de l'image.");
  } finally {
    loadingEl.classList.add("d-none");
    generateLabel.classList.remove("d-none");
  }
}

// --- Modal / Lightbox ---
function setupLightbox() {
  const img      = document.getElementById("resultImg");
  const modal    = document.getElementById("imgModal");
  const modalImg = document.getElementById("imgModalContent");
  const closeBtn = document.getElementById("imgModalClose");

  img.onclick = function () {
    if (this.src && !this.classList.contains("d-none")) {
      modalImg.src = this.src;
      modal.style.display = "flex";
    }
  };
  closeBtn.onclick = function () {
    modal.style.display = "none";
  };
  modal.onclick = function (e) {
    if (e.target === modal) modal.style.display = "none";
  };
}

// --- Zoom + drag on lightbox ---
function setupLightboxZoom() {
  const modal    = document.getElementById("imgModal");
  const modalImg = document.getElementById("imgModalContent");
  const closeBtn = document.getElementById("imgModalClose");

  let zoomed = false;
  let dragging = false;
  let startX = 0, startY = 0;
  let baseX = 0, baseY = 0;

  function resetView() {
    zoomed = false;
    dragging = false;
    baseX = baseY = 0;
    modalImg.classList.remove("zoomed");
    modalImg.style.transform = "translate(0, 0)";
    modalImg.style.maxWidth = "90%";
    modalImg.style.maxHeight = "90%";
  }

  modalImg.addEventListener("click", (e) => {
    if (dragging) return;
    zoomed = !zoomed;
    if (zoomed) {
      modalImg.classList.add("zoomed");
      modalImg.style.maxWidth = "50%";
      modalImg.style.maxHeight = "50%";
      baseX = baseY = 0;
      modalImg.style.transform = "translate(0, 0)";
    } else {
      resetView();
    }
  });

  modalImg.addEventListener("mousedown", (e) => {
    if (!zoomed) return;
    dragging = true;
    startX = e.clientX - baseX;
    startY = e.clientY - baseY;
  });

  window.addEventListener("mouseup", () => { dragging = false; });

  window.addEventListener("mousemove", (e) => {
    if (!dragging || !zoomed) return;
    baseX = e.clientX - startX;
    baseY = e.clientY - startY;
    modalImg.style.transform = `translate(${baseX}px, ${baseY}px)`;
  });

  closeBtn.addEventListener("click", () => {
    modal.style.display = "none";
    resetView();
  });
  modal.addEventListener("click", (e) => {
    if (e.target === modal) {
      modal.style.display = "none";
      resetView();
    }
  });
}

// --- Download & Share ---
function setupImageActions() {
  const resultImg    = document.getElementById("resultImg");
  const imageActions = document.getElementById("imageActions");
  const downloadBtn  = document.getElementById("downloadBtn");
  const shareBtn     = document.getElementById("shareBtn");

  // Show action buttons when image loads
  resultImg.addEventListener("load", () => {
    if (resultImg.src && !resultImg.classList.contains("d-none")) {
      if (imageActions) {
        imageActions.classList.remove("d-none");
        imageActions.classList.add("d-flex");
      }
    }
  });

  // Hide action buttons before generation
  document.getElementById("filterForm").addEventListener("submit", () => {
    if (imageActions) {
      imageActions.classList.add("d-none");
      imageActions.classList.remove("d-flex");
    }
  });

  downloadBtn?.addEventListener("click", () => {
    if (!resultImg.src) return;
    const a = document.createElement("a");
    a.href = resultImg.src;
    a.download = "image-veec.png";
    document.body.appendChild(a);
    a.click();
    a.remove();
  });

  shareBtn?.addEventListener("click", async () => {
    if (!resultImg.src) return;
    try {
      const resp = await fetch(resultImg.src, { cache: "no-store" });
      const blob = await resp.blob();
      const file = new File([blob], "image-veec.png", { type: blob.type || "image/png" });

      if (navigator.canShare && navigator.canShare({ files: [file] })) {
        await navigator.share({ title: "Comm' VEEC", text: "Voici l'image générée", files: [file] });
        return;
      }
      if (navigator.share) {
        await navigator.share({ title: "Comm' VEEC", text: "Voici l'image générée", url: resultImg.src });
        return;
      }
      // Fallback: download
      const a = document.createElement("a");
      a.href = resultImg.src;
      a.download = "image-veec.png";
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (e) {
      console.warn("Partage indisponible, fallback download.", e);
    }
  });
}

// --- Boot ---
document.addEventListener("DOMContentLoaded", async function () {
  // Dates par défaut = week-end courant
  const weekend = getWeekendDates();
  document.getElementById("date_start").value = weekend.saturday;
  document.getElementById("date_end").value   = weekend.sunday;

  syncEndToNextDay({ force: false });

  document.getElementById("date_start").addEventListener("change", () => {
    syncEndToNextDay({ force: true });
  });
  document.getElementById("date_end").addEventListener("change", () => {
    const start = document.getElementById("date_start").value;
    const end   = document.getElementById("date_end").value;
    if (start && end && end < start) syncEndToNextDay({ force: true });
  });

  await loadTemplates();
  await loadCategoriesForSeason();
  document.getElementById("saison")?.addEventListener("change", loadCategoriesForSeason);

  document.getElementById("filterForm").addEventListener("submit", submitForm);

  setupLightbox();
  setupLightboxZoom();
  setupImageActions();
});
