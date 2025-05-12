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
    children: [
      {
        name: "account",
        path: "account/",
        component: () => import("layouts/AccountLayout.vue"),
        children: [
          {
            name: "account-settings",
            path: "account-settings",
            component: () => import("pages/account/AccountSettingsPage.vue"),
            meta: {
              header: "Account settings",
            },
          },
          {
            name: "account-change-password",
            path: "account-change-password",
            component: () => import("pages/account/AccountChangePasswordPage.vue"),
            meta: {
              header: "Change password",
            },
          },
          {
            name: "account-security",
            path: "account-security",
            component: () => import("pages/account/AccountSecurityPage.vue"),
            meta: {
              header: "Account security",
            },
          },
        ],
      },
      {
        path: "",
        component: () => import("pages/IndexPage.vue"),
        meta: {
          header: "Home page",
        },
      },
    ],
  },
  // Always leave this as the last one
  {
    path: "/:catchAll(.*)*",
    component: () => import("pages/ErrorNotFound.vue"),
  },
];

export default routes;
