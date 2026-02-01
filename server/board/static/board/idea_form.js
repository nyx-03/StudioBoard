(function () {
  const select = document.querySelector('select[name="template_id"]');
  const md = document.querySelector('textarea[name="body_md"]');
  const status = document.getElementById('tplStatus');

  if (!select || !md) return;

  let lastAutoFill = "";

  function setStatus(msg) {
    if (!status) return;
    status.textContent = msg || "";
  }

  async function fetchTemplateBody(boardId, templateId) {
    const url = `/b/${boardId}/templates/preview/?id=${encodeURIComponent(templateId)}`;
    const res = await fetch(url, {
      headers: { "X-Requested-With": "XMLHttpRequest" }
    });
    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error(data.error || "fetch_failed");
    return data.template.body_md || "";
  }

  function getBoardIdFromPath() {
    const parts = window.location.pathname.split("/").filter(Boolean);
    const i = parts.indexOf("b");
    if (i !== -1 && parts[i + 1] && /^\d+$/.test(parts[i + 1])) {
      return parts[i + 1];
    }
    return null;
  }

  async function onTemplateChange() {
    const templateId = select.value;
    const boardId = getBoardIdFromPath();

    if (!templateId || !boardId) {
      if (md.value === lastAutoFill) {
        md.value = "";
        lastAutoFill = "";
      }
      setStatus("");
      return;
    }

    try {
      setStatus("Chargement du template…");
      const body = await fetchTemplateBody(boardId, templateId);

      const hasUserText = md.value.trim().length > 0 && md.value !== lastAutoFill;
      if (hasUserText) {
        const ok = confirm("Remplacer le contenu Markdown actuel par le template sélectionné ?");
        if (!ok) {
          setStatus("Template non appliqué.");
          return;
        }
      }

      md.value = body;
      lastAutoFill = body;
      setStatus("Template prévisualisé dans le Markdown.");
    } catch (e) {
      console.error(e);
      setStatus("Impossible de charger le template (voir console).");
    }
  }

  select.addEventListener("change", onTemplateChange);
})();