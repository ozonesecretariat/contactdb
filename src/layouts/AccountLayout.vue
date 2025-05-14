<template>
  <q-page>
    <q-card class="account-card">
      <q-card-section>
        <h4 class="q-my-none">
          {{ route.meta.header }}
        </h4>
      </q-card-section>
      <q-card-section>
        <router-view />
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script setup lang="ts">
import { useRoute } from "vue-router";

const route = useRoute();
</script>

<style scoped lang="scss">
.account-card {
  width: 100%;
  height: min-content;
  margin: 20px;
  padding: 20px;
  max-width: 768px;
}
</style>
