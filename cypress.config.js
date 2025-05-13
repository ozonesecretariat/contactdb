import { defineConfig } from "cypress";
import verifyDownloadTasks from "cy-verify-downloads";
import { rmSync, readdirSync } from "fs";

export default defineConfig({
  chromeWebSecurity: false,
  e2e: {
    baseUrl: "http://localhost:8080",
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
