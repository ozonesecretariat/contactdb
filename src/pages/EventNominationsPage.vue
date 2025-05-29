<template>
  <q-page>
    <div class="q-pa-lg">
      <q-table
        :rows="nominations"
        :columns="columns"
        row-key="id"
        :loading="isLoading"
        :filter="filter"
      >
        <template v-slot:top>
          <q-space />
          <q-input
            v-model="filter"
            placeholder="Search"
            dense
            debounce="300"
          >
            <template v-slot:append>
              <q-icon name="search" />
            </template>
          </q-input>
        </template>
      </q-table>
    </div>
  </q-page>
</template>

<script lang="ts">
import { defineComponent, ref, computed } from 'vue';
import { useAsyncState } from "@vueuse/core";
import { api } from "boot/axios";
import { QTableColumn } from 'quasar';
import type { EventNomination } from 'src/types/registration';

export default defineComponent({
  name: 'EventNominationsPage',
  props: {
    invitationToken: {
      type: String,
      required: true
    }
  },

  setup(props) {
    const filter = ref('');

    const columns: QTableColumn[] = [
      {
        name: 'contact',
        required: true,
        label: 'Contact',
        align: 'left',
        field: (row: EventNomination) => `${row.contact.firstName} ${row.contact.lastName}`,
        sortable: true
      },
      {
        name: 'organization',
        align: 'left',
        label: 'Organization',
        field: 'organization',
        sortable: true
      },
      {
        name: 'created_on',
        align: 'left',
        label: 'Registered On',
        field: 'created_on',
        sortable: true
      },
      {
        name: 'status',
        align: 'left',
        label: 'Status',
        field: 'status',
        sortable: true
      }
    ];

    const { isLoading, state } = useAsyncState(
      async () => (await api.get<EventNomination[]>(`/events/nominations/${props.invitationToken}/`)).data,
      []
    );

    const nominations = computed(() => {
      const text = filter.value.toLowerCase();
      return state.value.filter((nomination: EventNomination) =>
        nomination.contact.firstName.toLowerCase().includes(text) ||
        nomination.contact.lastName.toLowerCase().includes(text) ||
        nomination.organization.name.toLowerCase().includes(text) ||
        nomination.status.toLowerCase().includes(text)
      );
    });

    return {
      nominations,
      columns,
      isLoading,
      filter
    };
  }
});
</script>