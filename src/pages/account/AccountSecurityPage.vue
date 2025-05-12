<template>
  <manage-two-factor-page v-if="userStore.twoFactorEnabled" />
  <enable-two-factor-page v-else />
</template>

<script setup lang="ts">
import { useUserStore } from "stores/userStore";

import ManageTwoFactorPage from "pages/account/ManageTwoFactorPage.vue";
import EnableTwoFactorPage from "pages/account/EnableTwoFactorPage.vue";

const userStore = useUserStore();
</script>
