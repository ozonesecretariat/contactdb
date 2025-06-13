<template>
  <div class="flex column q-gutter-y-md">
    <div class="text-subtitle2">Ozone Secretariat</div>
    <div class="flex q-gutter-x-md">
      <q-input v-model="search" placeholder="Search" autofocus role="search" filled dense class="col-grow">
        <template #prepend>
          <q-icon name="search" />
        </template>
      </q-input>
      <q-btn icon="add" color="accent">Add Nomination</q-btn>
    </div>
    <div class="text-subtitle2 q-mt-xl">Current nominations</div>
    <q-table
      :rows="filteredNominations"
      :columns="columns"
      row-key="id"
      :loading="isLoadingNominations || isLoadingEvents"
      :pagination="{
        rowsPerPage: 15,
        sortBy: 'contact',
        descending: false,
      }"
      :dense="$q.screen.lt.lg"
      :grid="$q.screen.lt.md"
    >
      <template #header="props">
        <q-tr :props="props">
          <q-th v-for="col in props.cols" :key="col.name" :props="props">
            {{ col.label }}
            <q-tooltip v-if="col.tooltip">
              {{ col.tooltip }}
            </q-tooltip>
          </q-th>
        </q-tr>
      </template>

      <template #body-cell-actions="props">
        <q-td :props="props">
          <q-btn icon="edit" flat size="sm" round />
        </q-td>
      </template>
    </q-table>
  </div>
</template>

<script setup lang="ts">
import type { MeetingEvent } from "src/types/event";
import type { QTableColumnWithTooltip } from "src/types/quasar";
import type { Contact, EventNomination } from "src/types/registration";

import { useAsyncState } from "@vueuse/core";
import { useRouteQuery } from "@vueuse/router";
import { api } from "boot/axios";
import { useQuasar } from "quasar";
import { unaccentSearch } from "src/utils/search";
import { computed } from "vue";

interface GroupedEventNomination {
  contact: Contact;
  nominations: {
    [key: string]: EventNomination;
  };
}

const { invitationToken } = defineProps({
  invitationToken: {
    required: true,
    type: String,
  },
});

const $q = useQuasar();
const search = useRouteQuery("search", "");

const { isLoading: isLoadingNominations, state: nominations } = useAsyncState(
  async () => (await api.get<EventNomination[]>(`/events-nominations/${invitationToken}/`)).data,
  [],
);
const { isLoading: isLoadingEvents, state: events } = useAsyncState<MeetingEvent[]>(
  async () => (await api.get(`/events-nominations/${invitationToken}/events/`)).data,
  [],
);

const groupedNominations = computed(() => {
  const result: Record<number, GroupedEventNomination> = {};
  for (const nomination of nominations.value) {
    let obj = result[nomination.contact.id];
    if (!obj) {
      obj = {
        contact: nomination.contact,
        nominations: {},
      };
      result[nomination.contact.id] = obj;
    }
    obj.nominations[nomination.event.code] = nomination;
  }
  return Object.values(result);
});

const columns = computed(() => {
  const result: QTableColumnWithTooltip<GroupedEventNomination>[] = [
    {
      align: "left",
      field: (row) => row.contact.fullName,
      label: "Full name",
      name: "fullName",
      sortable: true,
    },
    {
      align: "left",
      field: (row) => row.contact.organization?.name ?? "",
      label: "Organization",
      name: "organization",
      sortable: true,
    },
  ];
  for (const event of events.value) {
    result.push({
      align: "left",
      field: (row) => row.nominations[event.code]?.status ?? "-",
      label: event.code,
      name: `eventCode-${event.code}`,
      sortable: true,
      tooltip: event.title,
    });
  }
  result.push({
    align: "right",
    field: () => "",
    label: "",
    name: "actions",
    sortable: false,
  });
  return result;
});

const filteredNominations = computed(() =>
  unaccentSearch(search.value, groupedNominations.value, (item) => [
    item.contact.firstName,
    item.contact.lastName,
    item.contact.fullName,
    item.contact.organization?.name,
  ]),
);
</script>
