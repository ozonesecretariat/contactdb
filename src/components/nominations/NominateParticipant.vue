<template>
  <q-card-section class="col-grow">
    <pre>{{ invitation.participant }}</pre>
  </q-card-section>
  <q-card-section class="modal-footer">
    <q-btn :to="{ name: 'verify-participant', params: { participantId: invitation.participantId } }">Back</q-btn>
    <q-btn color="accent" :loading="loading" @click="confirmNomination">Confirm nomination</q-btn>
  </q-card-section>
</template>

<script setup lang="ts">
import { useStorage } from "@vueuse/core";
import { useInvitationStore } from "stores/invitationStore";
import { ref } from "vue";
import { useRouter } from "vue-router";

const dontShowNominationConfirmation = useStorage("dontShowNominationConfirmation", false);
const router = useRouter();
const loading = ref(false);
const invitation = useInvitationStore();

async function confirmNomination() {
  loading.value = true;
  try {
    // TODO: add nomination to API/DB
    await invitation.loadNominations();
    if (dontShowNominationConfirmation.value) {
      await router.push({ name: "event-nominations" });
    } else {
      await router.push({ name: "confirm-nomination" });
    }
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped lang="scss"></style>
