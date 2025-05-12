import type { RouteRecordRaw } from "vue-router";

const routes: RouteRecordRaw[] = [
  {
    path: "/auth/",
    component: () => import("layouts/AuthLayout.vue"),
    children: [
      {
        name: "login",
        path: "login",
        component: () => import("pages/auth/LoginPage.vue"),
        meta: {
          header: "Login",
        },
      },
      {
        name: "password-reset",
        path: "password-reset",
        component: () => import("pages/auth/PasswordResetPage.vue"),
        meta: {
          header: "Password reset",
        },
      },
      {
        name: "password-reset-confirm",
        path: "password-reset-confirm",
        props: true,
        component: () => import("pages/auth/PasswordResetConfirmPage.vue"),
        meta: {
          header: "Password reset",
        },
      },
    ],
  },
  {
    path: "/",
    component: () => import("layouts/MainLayout.vue"),
    children: [{ path: "", component: () => import("pages/IndexPage.vue") }],
  },

  // Always leave this as the last one
  {
    path: "/:catchAll(.*)*",
    component: () => import("pages/ErrorNotFound.vue"),
  },
];

export default routes;
