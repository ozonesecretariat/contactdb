import type { AxiosError } from "axios";
import type { MenuSection } from "src/types/menu";

import { api, apiBase } from "boot/axios";
import { defineStore } from "pinia";
import { hasRoutePermission } from "src/router";

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
    allPages(state): MenuSection[] {
      return [
        {
          items: [
            {
              icon: "event",
              label: "Events",
              to: { name: "events" },
            },
            {
              icon: "qr_code_scanner",
              label: "Scan Pass",
              to: { name: "scan-pass" },
            },
            {
              icon: "payments",
              label: "DSA",
              to: { name: "dsa" },
            },
          ],
          name: "pages",
        },
        {
          items: [
            {
              href: `${apiBase}/admin/`,
              icon: "admin_panel_settings",
              label: "Admin",
              show: state.isStaff,
            },
          ],
          name: "admin",
        },
      ];
    },
    availablePages(): MenuSection[] {
      const result: MenuSection[] = this.allPages.map((section) => ({
        items: section.items.filter((item) => {
          if (item.to) {
            const resolvedRoute = this.router.resolve(item.to);
            if (!hasRoutePermission(resolvedRoute.matched)) {
              return false;
            }
          }
          return item.show ?? true;
        }),
        name: section.name,
      }));

      return result.filter((section) => section.items.length > 0);
    },
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
