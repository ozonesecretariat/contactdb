<template>
  <q-layout view="hHh lpR fFf" class="bg-grey-2">
    <q-page-container class="token-container">
      <q-page class="q-pa-lg">
        <h1 class="text-secondary">
          {{ route.meta.header }}
        </h1>
        <p class="text-subtitle1">
          {{ route.meta.subtitle }}
        </p>
        <div class="bg-white q-pa-lg rounded-borders">
          <router-view />
        </div>
      </q-page>
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { useRoute } from "vue-router";

const route = useRoute();
</script>

<style scoped lang="scss">
.token-container {
  max-width: 80rem;
  margin: auto;
}
</style>
