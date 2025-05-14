import verifyDownloadTasks from "cy-verify-downloads";
import { defineConfig } from "cypress";
import { readdirSync, rmSync } from "fs";

export default defineConfig({
  chromeWebSecurity: false,
  e2e: {
    baseUrl: "http://localhost:8080",
    setupNodeEvents(on, config) {
      on("task", verifyDownloadTasks);
      on("task", {
        cleanDownloadsFolder() {
          rmSync(config.downloadsFolder, {
            force: true,
            recursive: true,
          });
          return null;
        },
        downloads() {
          return readdirSync(config.downloadsFolder);
        },
        log(message) {
          // eslint-disable-next-line no-console
          console.log(message);
          return null;
        },
      });
      return config;
    },
    viewportHeight: 1080,
    viewportWidth: 1920,
  },
});
