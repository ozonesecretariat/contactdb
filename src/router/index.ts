import { defineRouter } from "#q-app/wrappers";
import { createMemoryHistory, createRouter, createWebHashHistory, createWebHistory } from "vue-router";
import routes from "./routes";
import { useUserStore } from "stores/userStore";
import { useQuasar } from "quasar";

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
    scrollBehavior: () => ({ left: 0, top: 0 }),
    routes,

    // Leave this as is and make changes in quasar.conf.js instead!
    // quasar.conf.js -> build -> vueRouterMode
    // quasar.conf.js -> build -> publicPath
    history: createHistory(process.env.VUE_ROUTER_BASE),
  });

  router.beforeEach(async (to) => {
    const userStore = useUserStore();
    const $q = useQuasar();

    if (!userStore.initialized) {
      $q.loading.show();
      await userStore.fetchUser();
      $q.loading.hide();
    }

    for (const route of to.matched) {
      const hasPermissions = (route.meta.requiredPermissions ?? []).every((permission) =>
        userStore.permissions.includes(permission),
      );

      if (to.meta.requireAuthentication && !userStore.isLoggedIn) {
        $q.notify({
          type: "warning",
          message: "Must be logged in to view this page.",
        });
        return { name: "login" };
      }

      if (to.meta.requireAnonymous && userStore.isLoggedIn) {
        return { name: "home" };
      }

      if (!hasPermissions) {
        $q.notify({
          type: "warning",
          message: "Your account does not have the required permissions to access this page.",
        });
        return { name: "home" };
      }
    }

    if (!userStore.twoFactorEnabled && userStore.appSettings.require2fa && to.name !== "account-security") {
      $q.notify({
        type: "info",
        message: "Two factor authentication is required for this account. Please update your settings to continue.",
      });
      return { name: "account-security" };
    }

    return true;
  });

  return router;
});
