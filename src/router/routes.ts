import type { RouteRecordRaw } from "vue-router";

const routes: RouteRecordRaw[] = [
  {
    path: "/auth/",
    component: () => import("layouts/AuthLayout.vue"),
    meta: {
      requireAnonymous: true,
    },
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
    meta: {
      requireAuthentication: true,
    },
    children: [
      {
        name: "account",
        path: "account/",
        component: () => import("layouts/AccountLayout.vue"),
        children: [
          {
            name: "account-settings",
            path: "settings",
            component: () => import("pages/account/AccountSettingsPage.vue"),
            meta: {
              header: "Account settings",
            },
          },
          {
            name: "account-change-password",
            path: "password",
            component: () => import("pages/account/AccountChangePasswordPage.vue"),
            meta: {
              header: "Change password",
            },
          },
          {
            name: "account-security",
            path: "security",
            component: () => import("pages/account/AccountSecurityPage.vue"),
            meta: {
              header: "Account security",
            },
          },
        ],
      },
      {
        name: "events",
        path: "events",
        component: () => import("pages/EventsPage.vue"),
        meta: {
          header: "Events",
          requirePermissions: ["events.view_event"],
        },
      },
      {
        name: "home",
        path: "",
        component: () => import("pages/HomePage.vue"),
        meta: {
          header: "",
          // Home page should be accessible to every authenticated user,
          // otherwise it will trigger an infinite redirect.
          requirePermissions: [],
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
