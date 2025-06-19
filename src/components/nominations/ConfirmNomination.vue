<template>
  <q-card-section class="col-grow">
    <p>Please send your official nomination letter to the Secretariat to complete the registration.</p>
  </q-card-section>
  <q-card-section class="modal-footer">
    <q-checkbox v-model="dontShowNominationConfirmation" label="Don't show this message again" />
    <q-btn color="accent" :to="{ name: 'event-nominations' }">Close</q-btn>
  </q-card-section>
</template>

<script setup lang="ts">
import { useStorage } from "@vueuse/core";

const dontShowNominationConfirmation = useStorage("dontShowNominationConfirmation", false);
</script>

<style scoped lang="scss"></style>
