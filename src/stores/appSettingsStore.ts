import { api } from "boot/axios";
import { defineStore } from "pinia";

export const useAppSettingsStore = defineStore("appSettings", {
  actions: {
    async load() {
      Object.assign(this, (await api.get("/app-settings/")).data);
      this.initialized = true;
    },
  },
  state: () => ({
    environmentName: "",
    initialized: false,
    require2fa: false,
  }),
});
