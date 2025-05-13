import { api } from "boot/axios";
import { defineStore } from "pinia";
import type { AxiosError } from "axios";

const initialState = {
  initialized: false,
  email: "",
  firstName: null as string | null,
  lastName: null as string | null,
  isStaff: false,
  isSuperuser: false,
  isActive: false,
  twoFactorEnabled: false,
  permissions: [] as string[],
  roles: [] as string[],
};

export const useUserStore = defineStore("user", {
  state: () => structuredClone(initialState),
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
  actions: {
    async load() {
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
      } finally {
        this.initialized = true;
      }
    },
    async logoutUser() {
      await api.post("/auth/logout/");
      Object.assign(this, initialState);
    },
  },
});
