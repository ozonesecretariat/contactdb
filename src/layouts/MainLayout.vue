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
            <q-list>
              <q-item v-close-popup clickable :to="{ name: 'account-settings' }">
                <q-item-section>Account settings</q-item-section>
              </q-item>
              <q-item v-close-popup clickable :to="{ name: 'account-security' }">
                <q-item-section>Account security</q-item-section>
              </q-item>
              <q-item v-close-popup clickable :to="{ name: 'account-change-password' }">
                <q-item-section>Change password</q-item-section>
              </q-item>
              <q-separator />
              <q-item v-close-popup clickable @click="logout">
                <q-item-section>Logout</q-item-section>
              </q-item>
            </q-list>
          </q-menu>
        </q-btn>
      </q-toolbar>
    </q-header>

    <q-drawer v-model="leftDrawerOpen" side="left" bordered overlay>
      <!-- drawer content -->
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useUserStore } from "stores/userStore";
import { api } from "boot/axios";
import { useRoute, useRouter } from "vue-router";
import { useQuasar } from "quasar";

const $q = useQuasar();
const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const leftDrawerOpen = ref(false);

function toggleLeftDrawer() {
  leftDrawerOpen.value = !leftDrawerOpen.value;
}

async function logout() {
  $q.loading.show();
  try {
    await api.post("/auth/logout/");
    await router.push({ name: "login" });
  } finally {
    $q.loading.hide();
  }
}
</script>
