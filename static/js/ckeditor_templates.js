"use strict";

(function initTemplates() {
  const { CKEDITOR } = window;
  if (!CKEDITOR) {
    return;
  }

  const templates = JSON.parse(document.getElementById("ckeditor-templates")?.textContent || "null");
  if (templates) {
    CKEDITOR.addTemplates("default", {
      imagesPath: CKEDITOR.getUrl(`${CKEDITOR.plugins.getPath("templates")}templates/images/`),
      templates,
    });
  }
})();
