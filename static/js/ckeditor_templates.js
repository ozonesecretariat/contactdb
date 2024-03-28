(function () {
  const CKEDITOR = window.CKEDITOR;
  if (!CKEDITOR) return;

  const templates = JSON.parse(document.getElementById("ckeditor-templates")?.textContent || "null");
  if (templates) {
    console.log("Adding templates", templates);
    CKEDITOR.addTemplates("default", {
      imagesPath: CKEDITOR.getUrl(CKEDITOR.plugins.getPath("templates") + "templates/images/"),
      templates,
    });
  }
})();
