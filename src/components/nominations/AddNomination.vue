<template>
  <q-btn icon="add" color="accent" :to="{ name: 'find-participant' }">Add Nomination</q-btn>
  <q-dialog :model-value="modalOpen" persistent>
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
import { computed } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();
const modalOpen = computed(() => route.matched.length >= 3);
</script>

<style scoped lang="scss">
.nomination-modal {
  max-width: 90rem;
  display: flex;
  flex-direction: column;
}
</style>
