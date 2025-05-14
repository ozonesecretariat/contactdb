import type { AxiosError } from "axios";

import { api } from "boot/axios";
import { defineStore } from "pinia";

const initialState = {
  email: "",
  firstName: null as null | string,
  initialized: false,
  isActive: false,
  isStaff: false,
  isSuperuser: false,
  lastName: null as null | string,
  permissions: [] as string[],
  roles: [] as string[],
  twoFactorEnabled: false,
};

export const useUserStore = defineStore("user", {
  actions: {
    async load() {
      try {
        const response = (await api.get("/auth/user/")).data;
        Object.assign(this, response);
      } catch (e) {
        switch ((e as AxiosError).status) {
          case 401:
          case 403:
            break;
          default:
            throw e;
        }
      } finally {
        this.initialized = true;
      }
    },
    async logoutUser() {
      await api.post("/auth/logout/");
      Object.assign(this, initialState);
    },
  },
  getters: {
    fullName(state) {
      if (!state.firstName && !state.lastName) {
        return state.email;
      }

      return `${state.firstName} ${state.lastName}`;
    },
    initials(state) {
      const parts: (string | undefined)[] = [];
      if (state.firstName) {
        parts.push(state.firstName[0]);
      }
      if (state.lastName) {
        parts.push(state.lastName[0]);
      }

      if (parts.length === 0) {
        parts.push(state.email[0]);
      }

      return parts
        .filter((p) => p)
        .join("")
        .toUpperCase();
    },
    isLoggedIn(state) {
      return state.email && state.isActive;
    },
  },
  state: () => structuredClone(initialState),
});
