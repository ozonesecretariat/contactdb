<template>
  <q-card-section class="col-grow">
    <pre>{{ invitation.participant }}</pre>
  </q-card-section>
  <q-card-section class="modal-footer">
    <q-btn :to="{ name: 'find-participant' }">Back</q-btn>
    <q-btn color="accent" :to="{ name: 'nominate-participant', params: { participantId } }">Next</q-btn>
  </q-card-section>
</template>

<script setup lang="ts">
import { useInvitationStore } from "stores/invitationStore";
const invitation = useInvitationStore();
</script>

<style scoped lang="scss"></style>
