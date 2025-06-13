<template>
  <div class="flex column q-gutter-y-md">
    <div class="text-subtitle2">Ozone Secretariat</div>
    <div class="flex q-gutter-x-md">
      <q-input
        v-model="filter"
        placeholder="Search"
        debounce="200"
        autofocus
        role="search"
        standout
        dense
        class="col-grow"
      >
        <template #prepend>
          <q-icon name="search" />
        </template>
      </q-input>
      <q-btn icon="add" color="accent">Add Nomination</q-btn>
    </div>
    <div class="text-subtitle2 q-mt-xl">Current nominations</div>
    <q-table :rows="filteredNominations" :columns="columns" row-key="id" :loading="isLoadingNominations" />
  </div>
</template>

<script setup lang="ts">
import type { QTableColumn } from "quasar";
import type { EventNomination } from "src/types/registration";

import { useAsyncState } from "@vueuse/core";
import { api } from "boot/axios";
import { computed, ref } from "vue";

const props = defineProps({
  invitationToken: {
    required: true,
    type: String,
  },
});

const filter = ref("");

const columns: QTableColumn[] = [
  {
    align: "left",
    field: (row: EventNomination) => `${row.contact.firstName} ${row.contact.lastName}`,
    label: "Contact",
    name: "contact",
    required: true,
    sortable: true,
  },
  {
    align: "left",
    field: "organization",
    label: "Organization",
    name: "organization",
    sortable: true,
  },
  {
    align: "left",
    field: "created_on",
    label: "Registered On",
    name: "created_on",
    sortable: true,
  },
  {
    align: "left",
    field: "status",
    label: "Status",
    name: "status",
    sortable: true,
  },
];

const { isLoading: isLoadingNominations, state: nominations } = useAsyncState(
  async () => (await api.get<EventNomination[]>(`/events/nominations/${props.invitationToken}/`)).data,
  [],
);
//
// const { isLoading: isLoadingContacts, state: availableContacts } = useAsyncState(
//   async () => (await api.get(`/events/nominations/${props.invitationToken}/available_contacts/`)).data,
//   [],
// );

const filteredNominations = computed(() => {
  const text = filter.value.toLowerCase();
  return nominations.value.filter(
    (nomination: EventNomination) =>
      nomination.contact.firstName.toLowerCase().includes(text) ||
      nomination.contact.lastName.toLowerCase().includes(text) ||
      nomination.organization.name.toLowerCase().includes(text) ||
      nomination.status.toLowerCase().includes(text),
  );
});
</script>
