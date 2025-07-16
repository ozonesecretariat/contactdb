<template>
  <q-btn icon="add" color="accent" :to="{ name: 'find-participant' }">Add Nomination</q-btn>
  <q-dialog v-if="invitation.initialized" :model-value="modalOpen" persistent>
    <q-card class="nomination-modal">
      <q-card-section class="modal-header">
        <div class="text-h6">{{ route.meta.modalHeader }}</div>
        <q-space />
        <q-btn icon="close" flat round dense :to="{ name: 'event-nominations' }" />
      </q-card-section>
      <router-view />
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { useInvitationStore } from "stores/invitationStore";
import { computed } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();
const modalOpen = computed(() => route.matched.length >= 3);
const invitation = useInvitationStore();
</script>

<style scoped lang="scss">
.nomination-modal {
  max-width: 55rem;
  width: 100%;
  display: flex;
  flex-direction: column;
}
</style>
