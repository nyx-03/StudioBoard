(function () {
  function getCookie(name) {
    const v = `; ${document.cookie}`;
    const parts = v.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return null;
  }

  function getBoardIdFromPath() {
    const parts = window.location.pathname.split("/").filter(Boolean);
    const i = parts.indexOf("b");
    if (i !== -1 && parts[i + 1] && /^\d+$/.test(parts[i + 1])) return parts[i + 1];
    return null;
  }

  function debounce(fn, ms) {
    let t = null;
    return function (...args) {
      clearTimeout(t);
      t = setTimeout(() => fn.apply(this, args), ms);
    };
  }

  async function renderMarkdown(boardId, bodyMd) {
    const url = `/b/${boardId}/md/preview/`;
    const csrftoken = getCookie("csrftoken");

    const form = new URLSearchParams();
    form.set("body_md", bodyMd || "");

    const res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        "X-CSRFToken": csrftoken || "",
        "X-Requested-With": "XMLHttpRequest"
      },
      body: form.toString()
    });

    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error(data.error || "preview_failed");
    return data.html || "";
  }

  function initOne(textarea) {
    const targetSelector = textarea.getAttribute("data-md-preview-target");
    if (!targetSelector) return;

    const preview = document.querySelector(targetSelector);
    if (!preview) return;

    const boardId = getBoardIdFromPath();
    if (!boardId) return;

    const setLoading = (on) => {
      preview.classList.toggle("md-preview-loading", !!on);
    };

    const update = debounce(async () => {
      try {
        setLoading(true);
        const html = await renderMarkdown(boardId, textarea.value);
        preview.innerHTML = html || '<span class="md-empty">Aperçu vide.</span>';
      } catch (e) {
        console.error(e);
        preview.innerHTML = '<span class="md-error">Impossible de générer l’aperçu (voir console).</span>';
      } finally {
        setLoading(false);
      }
    }, 250);

    textarea.addEventListener("input", update);
    // rendu initial
    update();
  }

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("textarea[data-md-preview-target]").forEach(initOne);
  });
})();