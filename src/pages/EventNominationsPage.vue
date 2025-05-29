<template>
  <q-page>
    <div class="q-pa-lg">
      <q-table :rows="nominations" :columns="columns" row-key="id" :loading="isLoading" :filter="filter">
        <template #top>
          <q-space />
          <q-input v-model="filter" placeholder="Search" dense debounce="300">
            <template #append>
              <q-icon name="search" />
            </template>
          </q-input>
        </template>
      </q-table>
    </div>
  </q-page>
</template>

<script lang="ts">
import type { QTableColumn } from "quasar";
import type { EventNomination } from "src/types/registration";

import { useAsyncState } from "@vueuse/core";
import { api } from "boot/axios";
import { computed, defineComponent, ref } from "vue";

export default defineComponent({
  name: "EventNominationsPage",
  props: {
    invitationToken: {
      required: true,
      type: String,
    },
  },

  setup(props) {
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

    const { isLoading, state } = useAsyncState(
      async () => (await api.get<EventNomination[]>(`/events/nominations/${props.invitationToken}/`)).data,
      [],
    );

    const { isLoading: loadingContacts, state: availableContacts } = useAsyncState(
      async () => (await api.get(`/events/nominations/${props.invitationToken}/available_contacts/`)).data,
      [],
    );

    const nominations = computed(() => {
      const text = filter.value.toLowerCase();
      return state.value.filter(
        (nomination: EventNomination) =>
          nomination.contact.firstName.toLowerCase().includes(text) ||
          nomination.contact.lastName.toLowerCase().includes(text) ||
          nomination.organization.name.toLowerCase().includes(text) ||
          nomination.status.toLowerCase().includes(text),
      );
    });

    return {
      availableContacts,
      columns,
      filter,
      isLoading,
      loadingContacts,
      nominations,
    };
  },
});
</script>
