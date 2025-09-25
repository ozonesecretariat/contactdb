<template>
  <q-layout view="hHh lpR fFf">
    <q-header elevated class="bg-primary text-white">
      <q-toolbar class="q-gutter-sm q-pa-xs">
        <q-btn dense flat round icon="menu" @click="toggleLeftDrawer" />

        <q-toolbar-title>
          {{ appSettingsStore.appTitle }}
          <template v-if="route.meta.header">&middot; {{ route.meta.header }}</template>
        </q-toolbar-title>
        <q-space />

        <q-btn round flat @click="toggleDarkMode">
          <q-avatar size="sm">
            <q-icon :name="isDarkMode ? 'dark_mode' : 'light_mode'" />
          </q-avatar>
        </q-btn>
        <q-btn round flat :data-user-email="userStore.email">
          <q-avatar color="secondary">
            {{ userStore.initials }}
          </q-avatar>
          <q-menu>
            <menu-list :items="menuItems" />
          </q-menu>
        </q-btn>
      </q-toolbar>
    </q-header>

    <q-drawer v-model="leftDrawerOpen" side="left" bordered>
      <div class="row q-pa-md">
        <ozone-logo />
      </div>
      <q-separator />
      <menu-list :items="drawerItems" />
    </q-drawer>
    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { useStorage } from "@vueuse/core";
import { apiBase } from "boot/axios";
import MenuList from "components/MenuList.vue";
import OzoneLogo from "components/OzoneLogo.vue";
import { useQuasar } from "quasar";
import { useAppSettingsStore } from "stores/appSettingsStore";
import { useUserStore } from "stores/userStore";
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

const $q = useQuasar();
const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const leftDrawerOpen = useStorage("leftDrawerOpen", true);
const isDarkMode = useStorage<boolean>("isDarkMode", window.matchMedia("(prefers-color-scheme: dark)").matches);
const appSettingsStore = useAppSettingsStore();

function toggleDarkMode() {
  isDarkMode.value = !isDarkMode.value;
  $q.dark.set(isDarkMode.value);
}
$q.dark.set(isDarkMode.value);

const menuItems = computed(() => [
  {
    items: [
      {
        icon: "account_circle",
        label: "Account settings",
        to: { name: "account-settings" },
      },
      {
        icon: "security",
        label: "Account security",
        to: { name: "account-security" },
      },
      {
        icon: "password",
        label: "Change password",
        to: { name: "account-change-password" },
      },
    ],
    name: "account",
  },
  {
    items: [
      {
        click: logout,
        icon: "logout",
        label: "Log out",
      },
    ],
    name: "other",
  },
]);

const drawerItems = computed(() => [
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
        show: userStore.isStaff,
      },
      {
        click: logout,
        icon: "logout",
        label: "Log out",
      },
    ],
    name: "other",
  },
]);

async function logout() {
  $q.loading.show();
  try {
    await userStore.logoutUser();
    await router.push({ name: "login" });
  } finally {
    $q.loading.hide();
  }
}

function toggleLeftDrawer() {
  leftDrawerOpen.value = !leftDrawerOpen.value;
}
</script>
