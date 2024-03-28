function initPlaceholderSelect() {
  const CKEDITOR = window.CKEDITOR;

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
    init: function (editor) {
      const placeholders = [];

      const defaultConfig = {
        format: "[[%placeholder%]]",
        placeholders: [],
      };

      const config = CKEDITOR.tools.extend(defaultConfig, editor.config.placeholder_select || {}, true);

      for (let i = 0; i < config.placeholders.length; i++) {
        const placeholder = config.format.replace("%placeholder%", config.placeholders[i]);
        placeholders.push([placeholder, config.placeholders[i], config.placeholders[i]]);
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

        init: function () {
          this.startGroup("Placeholder");
          for (const i in placeholders) {
            this.add(placeholders[i][0], placeholders[i][1], placeholders[i][2]);
          }
        },

        onClick: function (value) {
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
