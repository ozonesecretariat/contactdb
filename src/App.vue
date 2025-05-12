<template>
  <router-view />
</template>

<script setup lang="ts">
import { useUserStore } from "stores/userStore";
import { onMounted } from "vue";
import { useQuasar } from "quasar";

const $q = useQuasar();
const userStore = useUserStore();

onMounted(async () => {
  $q.loading.show();
  await userStore.fetchUser();
  $q.loading.hide();
});
</script>
