// StudioBoard Kanban drag&drop + save badge

(function () {
  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
  }

  const cfg = window.STUDIOBOARD || {};
  const saveUrl = cfg.reorderUrl;
  const csrftoken = getCookie("csrftoken");

  const statusEl = document.getElementById("saveStatus");

  function setStatus(state, text) {
    if (!statusEl) return;

    statusEl.classList.remove("saving", "saved", "error");
    statusEl.classList.add("show");

    if (state) statusEl.classList.add(state);
    statusEl.textContent = text;

    if (state === "saved") {
      window.clearTimeout(window.__sbHideTimer);
      window.__sbHideTimer = window.setTimeout(() => {
        statusEl.classList.remove("show");
      }, 900);
    }
  }

  let saveTimer = null;

  function collectBoardState() {
    const columns = [];
    document.querySelectorAll(".cards[data-column-id]").forEach((colEl) => {
      const colId = parseInt(colEl.dataset.columnId, 10);
      const ideaIds = Array.from(colEl.querySelectorAll(".card[data-idea-id]")).map(
        (card) => parseInt(card.dataset.ideaId, 10)
      );
      columns.push({ id: colId, idea_ids: ideaIds });
    });
    return { columns };
  }

  function scheduleSave() {
    setStatus("saving", "Sauvegarde…");
    if (saveTimer) window.clearTimeout(saveTimer);
    saveTimer = window.setTimeout(saveNow, 300); // debounce
  }

  async function saveNow() {
    if (!saveUrl) {
      setStatus("error", "URL reorder manquante");
      return;
    }

    const payload = collectBoardState();

    try {
      const resp = await fetch(saveUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrftoken,
        },
        body: JSON.stringify(payload),
      });

      if (!resp.ok) {
        setStatus("error", `Erreur sauvegarde (${resp.status})`);
        console.error("Save failed", resp.status);
        return;
      }

      const data = await resp.json().catch(() => null);
      if (data && data.ok === false) {
        setStatus("error", "Erreur sauvegarde (serveur)");
        console.error("Server error", data);
        return;
      }

      setStatus("saved", "Sauvegardé");
    } catch (e) {
      setStatus("error", "Erreur réseau");
      console.error("Save error", e);
    }
  }

  function initSortable() {
    if (typeof Sortable === "undefined") {
      console.error("SortableJS not loaded");
      return;
    }

    document.querySelectorAll(".cards[data-column-id]").forEach((colEl) => {
      new Sortable(colEl, {
        group: "kanban",
        animation: 150,
        handle: ".drag-handle",
        draggable: ".card",
        ghostClass: "dragging",
        onEnd: scheduleSave,
        onAdd: scheduleSave,
        onUpdate: scheduleSave,
      });
    });
  }

  function initSearch() {
    const form = document.querySelector(".search");
    const searchInput = document.querySelector(".search-input");
    const clearBtn = document.querySelector(".search-clear");

    if (!form || !searchInput || !searchInput.form) return;

    function syncUI() {
      const has = !!(searchInput.value || "").trim();
      if (has) form.classList.add("has-query");
      else form.classList.remove("has-query");
    }

    let t = null;
    searchInput.addEventListener("input", () => {
      syncUI();
      window.clearTimeout(t);
      t = window.setTimeout(() => {
        searchInput.form.submit();
      }, 250);
    });

    searchInput.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        if ((searchInput.value || "").length) {
          e.preventDefault();
          searchInput.value = "";
          syncUI();
          searchInput.form.submit();
        }
      }
    });

    if (clearBtn) {
      clearBtn.addEventListener("click", () => {
        if ((searchInput.value || "").length) {
          searchInput.value = "";
          syncUI();
          searchInput.focus();
          searchInput.form.submit();
        }
      });
    }

    // initial state
    syncUI();
  }

  // Init
  function init() {
    initSortable();
    initSearch();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();