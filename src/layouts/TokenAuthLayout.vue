<template>
  <q-layout view="hHh lpR fFf" class="bg-grey-2">
    <q-page-container class="token-container">
      <q-page class="q-pa-lg">
        <div class="row q-gutter-md">
          <div class="col-2">
            <ozone-logo />
          </div>
          <h1 class="text-secondary col">
            {{ appSettingsStore.appTitle }}
          </h1>
        </div>
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
import OzoneLogo from "components/OzoneLogo.vue";
import { useAppSettingsStore } from "stores/appSettingsStore";

const appSettingsStore = useAppSettingsStore();
</script>

<style scoped lang="scss">
.token-container {
  max-width: 80rem;
  margin: auto;
}
</style>
