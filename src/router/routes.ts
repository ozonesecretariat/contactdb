import type { RouteRecordRaw } from "vue-router";

const dsaPermissions = [
  "events.view_registration",
  "events.view_dsa",
  "events.view_registrationtag",
  "events.view_event",
];

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
        ],
        component: () => import("pages/EventNominationsPage.vue"),
        meta: {
          header: "Meeting Registration",
          metaHeaders: {
            title: "Meeting Registration - Nominations",
          },
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
        component: () => import("pages/DashboardPage.vue"),
        meta: {
          header: "Dashboard",
          requirePermissions: ["events.view_event"],
        },
        name: "dashboard",
        path: "dashboard",
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
        component: () => import("pages/DelegatesPage.vue"),
        meta: {
          header: "Delegates",
          requirePermissions: dsaPermissions,
        },
        name: "delegates",
        path: "delegates",
        props: {
          columns: ["country", "title", "firstName", "lastName", "umojaTravel", "bp", "status", "tags"],
        },
      },
      {
        component: () => import("pages/DelegatesPage.vue"),
        meta: {
          header: "DSA",
          requirePermissions: dsaPermissions,
        },
        name: "dsa",
        path: "dsa",
        props: {
          columns: [
            "country",
            "title",
            "firstName",
            "lastName",
            "umojaTravel",
            "bp",
            "termExp",
            "cashCard",
            "status",
            "tags",
          ],
          disablePaidDsa: true,
          disableStatus: true,
          disableTag: true,
        },
      },
      {
        component: () => import("pages/DelegatesPage.vue"),
        meta: {
          header: "Paid",
          requirePermissions: dsaPermissions,
        },
        name: "paid",
        path: "paid",
        props: {
          disablePaidDsa: true,
          disableStatus: true,
          disableTag: true,
          downloadReport: true,
        },
      },
      {
        component: () => import("pages/ScanPassPage.vue"),
        meta: {
          header: "Scan Pass",
          requirePermissions: ["events.view_prioritypass"],
        },
        name: "scan-pass",
        path: "scan-pass",
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
