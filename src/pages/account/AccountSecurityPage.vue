<template>
  <manage-two-factor-page v-if="userStore.twoFactorEnabled" />
  <enable-two-factor-page v-else />
</template>

<script setup lang="ts">
import EnableTwoFactorPage from "pages/account/EnableTwoFactorPage.vue";
import ManageTwoFactorPage from "pages/account/ManageTwoFactorPage.vue";
import { useUserStore } from "stores/userStore";

const userStore = useUserStore();
</script>
