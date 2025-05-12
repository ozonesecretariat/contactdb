import { defineRouter } from "#q-app/wrappers";
import { createMemoryHistory, createRouter, createWebHashHistory, createWebHistory } from "vue-router";
import routes from "./routes";

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

  return createRouter({
    scrollBehavior: () => ({ left: 0, top: 0 }),
    routes,

    // Leave this as is and make changes in quasar.conf.js instead!
    // quasar.conf.js -> build -> vueRouterMode
    // quasar.conf.js -> build -> publicPath
    history: createHistory(process.env.VUE_ROUTER_BASE),
  });
});
