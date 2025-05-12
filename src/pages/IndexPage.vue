<template>
  <q-page class="row items-center justify-evenly">Hello {{ userStore.fullName }}!</q-page>
</template>

<script setup lang="ts">
import { useUserStore } from "stores/userStore";

const userStore = useUserStore();
</script>
