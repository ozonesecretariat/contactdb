function initPlaceholderSelect() {
  const { CKEDITOR } = window;

  if (!CKEDITOR) {
    // Page doesn't have ckeditor, we don't need to do anything.
    return;
  }

  if (CKEDITOR.plugins.get("placeholder_select")) {
    // Already loaded
    return;
  }

  CKEDITOR.plugins.add("placeholder_select", {
    requires: ["richcombo"],
    init(editor) {
      const placeholders = [];

      const defaultConfig = {
        format: "[[%placeholder%]]",
        placeholders: [],
      };

      const config = CKEDITOR.tools.extend(defaultConfig, editor.config.placeholder_select || {}, true);

      for (const name of config.placeholders) {
        const placeholder = config.format.replace("%placeholder%", name);
        placeholders.push([placeholder, name, name]);
      }

      editor.ui.addRichCombo("placeholder_select", {
        label: "Placeholder",
        title: "Placeholder",
        voiceLabel: "Placeholder",
        className: "cke_format",
        multiSelect: false,
        panel: {
          css: [CKEDITOR.skin.getPath("editor")].concat(config.contentsCss),
          voiceLabel: editor.lang.panelVoiceLabel,
        },

        init() {
          this.startGroup("Placeholder");
          for (const attrs of placeholders) {
            this.add(...attrs);
          }
        },

        onClick(value) {
          editor.focus();
          editor.fire("saveSnapshot");
          editor.insertHtml(value);
          editor.fire("saveSnapshot");
        },
      });
    },
  });
}

document.addEventListener("DOMContentLoaded", initPlaceholderSelect);
