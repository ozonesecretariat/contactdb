<template>
  <q-layout view="hHh lpR fFf">
    <q-header elevated class="bg-primary text-white">
      <q-toolbar>
        <q-btn dense flat round icon="menu" @click="toggleLeftDrawer" />

        <q-toolbar-title>
          ContactDB
          <template v-if="route.meta.header">&middot; {{ route.meta.header }}</template>
        </q-toolbar-title>
        <q-space />

        <q-btn round flat>
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
      <q-list>
        <menu-list :items="drawerItems" />
      </q-list>
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

const menuItems = computed(() => [
  {
    label: "Admin",
    icon: "admin_panel_settings",
    href: apiBase,
    show: userStore.isStaff,
  },
  {
    label: "Admin separator",
    type: "separator" as const,
    show: userStore.isStaff,
  },
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
    label: "Logout",
    icon: "logout",
    click: logout,
  },
]);

const drawerItems = computed(() => [
  {
    label: "Events",
    icon: "event",
    to: { name: "events" },
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
