<template>
  <q-layout view="hHh lpR fFf" class="bg-grey-2">
    <q-page-container class="token-container">
      <q-page class="q-pa-lg">
        <h1 class="text-secondary">
          {{ appSettingsStore.appTitle }}
        </h1>
        <p class="text-subtitle1">
          {{ appSettingsStore.welcomeMessage }}
        </p>
        <div class="bg-white q-pa-lg rounded-borders">
          <router-view />
        </div>
      </q-page>
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { useAppSettingsStore } from "stores/appSettingsStore";

const appSettingsStore = useAppSettingsStore();
</script>

<style scoped lang="scss">
.token-container {
  max-width: 80rem;
  margin: auto;
}
</style>
