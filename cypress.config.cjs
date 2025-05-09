"use strict";

const { defineConfig } = require("cypress");
const { verifyDownloadTasks } = require("cy-verify-downloads");
const { rmSync, readdirSync } = require("fs");

module.exports = defineConfig({
  e2e: {
    baseUrl: "http://localhost:8000",
    viewportWidth: 1920,
    viewportHeight: 1080,
    setupNodeEvents(on, config) {
      on("task", verifyDownloadTasks);
      on("task", {
        log(message) {
          // eslint-disable-next-line no-console
          console.log(message);
          return null;
        },
        cleanDownloadsFolder() {
          rmSync(config.downloadsFolder, {
            recursive: true,
            force: true,
          });
          return null;
        },
        downloads() {
          return readdirSync(config.downloadsFolder);
        },
      });
      return config;
    },
  },
});
