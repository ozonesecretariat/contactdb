<template>
  <router-view />
</template>

<script setup lang="ts">
import { useMeta } from "quasar";
import { useRoute } from "vue-router";

const route = useRoute();

useMeta(() => ({
  title: `ContactDB - ${route.meta.header || "Home"}`,
  ...route.meta.metaHeaders,
}));
</script>
