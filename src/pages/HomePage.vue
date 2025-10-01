<template>
  <q-page class="q-pa-lg">
    <div>Welcome, {{ userStore.fullName }}</div>
  </q-page>
</template>

<script setup lang="ts">
import { useUserStore } from "stores/userStore";

const userStore = useUserStore();
</script>

<style scoped lang="scss"></style>
