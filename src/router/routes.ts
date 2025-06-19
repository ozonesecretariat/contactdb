import type { RouteRecordRaw } from "vue-router";

const routes: RouteRecordRaw[] = [
  {
    children: [
      {
        component: () => import("pages/auth/LoginPage.vue"),
        meta: {
          header: "Login",
        },
        name: "login",
        path: "login",
      },
      {
        component: () => import("pages/auth/PasswordResetPage.vue"),
        meta: {
          header: "Password reset",
        },
        name: "password-reset",
        path: "password-reset",
      },
      {
        component: () => import("pages/auth/PasswordResetConfirmPage.vue"),
        meta: {
          header: "Password reset",
        },
        name: "password-reset-confirm",
        path: "password-reset-confirm",
        props: true,
      },
    ],
    component: () => import("layouts/AuthLayout.vue"),
    meta: {
      requireAnonymous: true,
    },
    path: "/auth/",
  },
  {
    children: [
      {
        children: [
          {
            component: () => import("components/nominations/FindParticipant.vue"),
            meta: {
              modalHeader: "Add nomination",
            },
            name: "find-participant",
            path: "find",
          },
          {
            component: () => import("components/nominations/ParticipantForm.vue"),
            meta: {
              modalHeader: "Create participant",
            },
            name: "create-participant",
            path: "create",
          },
          {
            component: () => import("components/nominations/ParticipantForm.vue"),
            meta: {
              modalHeader: "Update participant",
            },
            name: "edit-participant",
            path: "edit/:participantId",
          },
          {
            component: () => import("components/nominations/NominateParticipant.vue"),
            meta: {
              modalHeader: "Nominate participant",
            },
            name: "nominate-participant",
            path: "nominate/:participantId",
          },
          {
            component: () => import("components/nominations/ConfirmNomination.vue"),
            meta: {
              modalHeader: "Nomination confirmed",
            },
            name: "confirm-nomination",
            path: "confirm",
          },
        ],
        component: () => import("pages/EventNominationsPage.vue"),
        meta: {
          header: "Meeting of Ozone Treaties",
          metaHeaders: {
            title: "ContactDB - Nominations",
          },
          subtitle:
            "The Meetings of Ozone Treaties are the cornerstone of the international effort to phase out ozone-depleting substances.",
        },
        name: "event-nominations",
        path: "nominations",
        props: true,
      },
    ],
    component: () => import("layouts/TokenAuthLayout.vue"),
    meta: {
      // Don't require either permission or anon access as this should be
      // accessible to anyone with the link.
    },
    path: "/token/:invitationToken",
  },
  {
    children: [
      {
        children: [
          {
            component: () => import("pages/account/AccountSettingsPage.vue"),
            meta: {
              header: "Account settings",
            },
            name: "account-settings",
            path: "settings",
          },
          {
            component: () => import("pages/account/AccountChangePasswordPage.vue"),
            meta: {
              header: "Change password",
            },
            name: "account-change-password",
            path: "password",
          },
          {
            component: () => import("pages/account/AccountSecurityPage.vue"),
            meta: {
              header: "Account security",
            },
            name: "account-security",
            path: "security",
          },
        ],
        component: () => import("layouts/AccountLayout.vue"),
        name: "account",
        path: "account/",
      },
      {
        component: () => import("pages/EventsPage.vue"),
        meta: {
          header: "Events",
          requirePermissions: ["events.view_event"],
        },
        name: "events",
        path: "events",
      },
      {
        component: () => import("pages/HomePage.vue"),
        meta: {
          header: "",
          // Home page should be accessible to every authenticated user,
          // otherwise it will trigger an infinite redirect.
          requirePermissions: [],
        },
        name: "home",
        path: "",
      },
    ],
    component: () => import("layouts/MainLayout.vue"),
    meta: {
      requireAuthentication: true,
    },
    path: "/",
  },
  // Always leave this as the last one
  {
    component: () => import("pages/ErrorNotFound.vue"),
    path: "/:catchAll(.*)*",
  },
];

export default routes;
