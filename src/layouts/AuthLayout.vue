<template>
  <q-layout view="hHh lpR fFf">
    <q-page-container>
      <q-page class="flex flex-center">
        <q-card class="login-card">
          <q-card-section class="text-center">
            <h4 class="q-mt-none q-mb-md">
              {{ route.meta.header }}
            </h4>
          </q-card-section>
          <q-card-section>
            <router-view />
          </q-card-section>
        </q-card>
      </q-page>
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { useRoute } from "vue-router";

const route = useRoute();
</script>

<style scoped lang="scss">
.login-card {
  width: 100%;
  padding: 20px;
  min-width: 400px;
  max-width: 500px;
}
</style>
