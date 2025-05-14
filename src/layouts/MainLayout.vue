<template>
  <q-layout view="hHh lpR fFf">
    <q-header elevated class="bg-primary text-white">
      <q-toolbar class="q-gutter-sm q-pa-xs">
        <q-btn dense flat round icon="menu" @click="toggleLeftDrawer" />

        <q-toolbar-title>
          ContactDB
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
      <menu-list :items="drawerItems" />
    </q-drawer>
    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useUserStore } from "stores/userStore";
import { apiBase } from "boot/axios";
import { useRoute, useRouter } from "vue-router";
import { useQuasar } from "quasar";
import { useStorage } from "@vueuse/core";
import MenuList from "components/MenuList.vue";

const $q = useQuasar();
const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const leftDrawerOpen = useStorage("leftDrawerOpen", true);
const isDarkMode = useStorage<boolean>("isDarkMode", window.matchMedia("(prefers-color-scheme: dark)").matches);

function toggleDarkMode() {
  isDarkMode.value = !isDarkMode.value;
  $q.dark.set(isDarkMode.value);
}
$q.dark.set(isDarkMode.value);

const menuItems = computed(() => [
  {
    label: "Account settings",
    icon: "account_circle",
    to: { name: "account-settings" },
  },
  {
    label: "Account security",
    icon: "security",
    to: { name: "account-security" },
  },
  {
    label: "Change password",
    icon: "password",
    to: { name: "account-change-password" },
  },
  {
    label: "Account separator",
    type: "separator" as const,
  },
  {
    label: "Log out",
    icon: "logout",
    click: logout,
  },
]);

const drawerItems = computed(() => [
  {
    label: "Home",
    icon: "home",
    to: { name: "home" },
  },
  {
    label: "Events",
    icon: "event",
    to: { name: "events" },
  },
  {
    label: "Account separator",
    type: "separator" as const,
  },
  {
    label: "Admin",
    icon: "admin_panel_settings",
    href: `${apiBase}/admin/`,
    show: userStore.isStaff,
  },
  ...menuItems.value,
]);

function toggleLeftDrawer() {
  leftDrawerOpen.value = !leftDrawerOpen.value;
}

async function logout() {
  $q.loading.show();
  try {
    await userStore.logoutUser();
    await router.push({ name: "login" });
  } finally {
    $q.loading.hide();
  }
}
</script>
