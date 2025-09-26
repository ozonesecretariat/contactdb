<template>
  <q-page class="q-pa-lg">
    <div>Welcome, {{ userStore.fullName }}</div>
  </q-page>
</template>

<script setup lang="ts">
import { useUserStore } from "stores/userStore";
import { computed, onBeforeMount } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const userStore = useUserStore();

const defaultPage = computed(() => userStore.availablePages[0]?.items[0]?.to);

onBeforeMount(() => {
  if (defaultPage.value) {
    router.replace(defaultPage.value);
  }
});
</script>

<style scoped lang="scss"></style>
