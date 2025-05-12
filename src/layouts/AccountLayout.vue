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
import { ref } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();
</script>

<style scoped lang="scss">
.login-card {
  width: 100%;
  padding: 20px;
  margin: 20px;
  min-width: 500px;
  max-width: 768px;
}
</style>
