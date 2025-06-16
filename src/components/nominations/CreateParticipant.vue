<template>
  <q-card-section class="col-grow"></q-card-section>
  <q-card-section class="modal-footer">
    <q-btn :to="{ name: 'verify-participant' }">Cancel</q-btn>
    <q-btn color="accent" :loading="loading" @click="createParticipant">Save</q-btn>
  </q-card-section>
</template>

<script setup lang="ts">
import { useInvitationStore } from "stores/invitationStore";
import { ref } from "vue";
import { useRouter } from "vue-router";

const loading = ref(false);
const invitation = useInvitationStore();
const router = useRouter();

async function createParticipant() {
  loading.value = true;
  try {
    // TODO: Create a new contact with the API
    await invitation.loadContacts();
    await router.push({ name: "find-participant" });
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped lang="scss"></style>
