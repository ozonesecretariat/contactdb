<template>
  <router-view />
</template>

<script setup lang="ts">
import { useMeta } from "quasar";
import { useAppSettingsStore } from "stores/appSettingsStore";
import { useRoute } from "vue-router";

const route = useRoute();
const appSettingsStore = useAppSettingsStore();

useMeta(() => ({
  title: `${appSettingsStore.appTitle} - ${route.meta.header || "Home"}`,
  ...route.meta.metaHeaders,
}));
</script>
