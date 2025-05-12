import { api } from "boot/axios";
import { defineStore } from "pinia";
import type { AxiosError } from "axios";

export const useUserStore = defineStore("user", {
  state: () => ({
    email: "",
    firstName: "",
    lastName: "",
    isStaff: false,
    isSuperuser: false,
    isActive: false,
    permissions: [] as string[],
    roles: [] as string[],
    appSettings: {
      environmentName: "",
    },
  }),
  getters: {
    fullName(state) {
      if (!state.firstName && !state.lastName) {
        return state.email;
      }

      return `${state.firstName} ${state.lastName}`;
    },
  },
  actions: {
    async fetchUser() {
      try {
        const response = (await api.get("/auth/user/")).data;
        Object.assign(this, response);
      } catch (e) {
        switch ((e as AxiosError).status) {
          case 403:
          case 401:
            break;
          default:
            throw e;
        }
      }
    },
  },
});
