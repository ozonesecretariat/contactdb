<template>
  <q-img v-if="$q.dark.isActive" src="~assets/logo-negative.png" fit="contain" />
  <q-img v-else src="~assets/logo.png" fit="contain" />
</template>

<script setup lang="ts">
import { useQuasar } from "quasar";

const $q = useQuasar();
</script>

<style scoped lang="scss"></style>
