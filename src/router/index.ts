import { defineRouter } from "#q-app/wrappers";
import { useQuasar } from "quasar";
import { useAppSettingsStore } from "stores/appSettingsStore";
import { useUserStore } from "stores/userStore";
import {
  createMemoryHistory,
  createRouter,
  createWebHashHistory,
  createWebHistory,
  type RouteLocationNormalizedGeneric,
  type RouteRecordNormalized,
} from "vue-router";

import routes from "./routes";

/**
 * Checks if the current user has the required permissions to access the given route.
 */
export function hasRoutePermission(matched: RouteRecordNormalized[]) {
  const userStore = useUserStore();
  return matched.every((route) => {
    if (route.meta.requireStaff && !userStore.isStaff) {
      return false;
    }

    if (route.meta.requireSuperuser && !userStore.isSuperuser) {
      return false;
    }

    return (route.meta.requirePermissions ?? []).every((permission) => userStore.permissions.includes(permission));
  });
}

/**
 * Guards navigation based on user authentication, permissions, and application settings.
 * Ensures the user meets the requirements for accessing the desired route.
 */
function permissionGuard(to: RouteLocationNormalizedGeneric) {
  const userStore = useUserStore();
  const appSettingsStore = useAppSettingsStore();
  const $q = useQuasar();
  const requireAuth = to.matched.some((route) => route.meta.requireAuthentication);

  // Check the matched routes and all of it's parents
  for (const route of to.matched) {
    if (route.meta.requireAuthentication && !userStore.isLoggedIn) {
      $q.notify({
        message: "Must be logged in to view this page.",
        type: "warning",
      });
      return { name: "login", query: { next: to.fullPath } };
    }

    if (route.meta.requireAnonymous && userStore.isLoggedIn) {
      return { name: "home" };
    }
  }

  if (!hasRoutePermission(to.matched)) {
    $q.notify({
      message: "Your account does not have the required permissions to access this page.",
      type: "warning",
    });
    return { name: "home" };
  }

  if (requireAuth && !userStore.twoFactorEnabled && appSettingsStore.require2fa && to.name !== "account-security") {
    $q.notify({
      message: "Two factor authentication is required for this account. Please update your settings to continue.",
      type: "info",
    });
    return { name: "account-security" };
  }

  return true;
}

// If not building with SSR mode, you can
// directly export the Router instantiation;
//
// The function below can be async too; either use
// async/await or return a Promise which resolves
// with the Router instance.

export default defineRouter((/* { store, ssrContext } */) => {
  let createHistory = null;
  if (process.env.SERVER) {
    createHistory = createMemoryHistory;
  } else if (process.env.VUE_ROUTER_MODE === "history") {
    createHistory = createWebHistory;
  } else {
    createHistory = createWebHashHistory;
  }

  const router = createRouter({
    // Leave this as is and make changes in quasar.conf.js instead!
    // quasar.conf.js -> build -> vueRouterMode
    // quasar.conf.js -> build -> publicPath
    history: createHistory(process.env.VUE_ROUTER_BASE),
    routes,

    scrollBehavior: () => ({ left: 0, top: 0 }),
  });

  router.beforeEach(permissionGuard);

  return router;
});
