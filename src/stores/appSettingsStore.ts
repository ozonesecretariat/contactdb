import { defineStore } from "pinia";
import { api } from "boot/axios";

export const useAppSettingsStore = defineStore("appSettings", {
  state: () => ({
    initialized: false,
    environmentName: "",
    require2fa: false,
  }),
  actions: {
    async load() {
      Object.assign(this, (await api.get("/app-settings/")).data);
      this.initialized = true;
    },
  },
});
