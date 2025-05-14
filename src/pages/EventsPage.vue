<template>
  <q-page class="q-pa-lg">
    <q-table
      :rows="events"
      :loading="isLoading"
      :columns="columns"
      :pagination="{
        rowsPerPage: 15,
        sortBy: 'code',
        descending: false,
      }"
    >
      <template #top-left>Events</template>
      <template #top-right>
        <q-input v-model="search" borderless dense debounce="200" placeholder="Search" autofocus role="search">
          <template #append>
            <q-icon name="search" />
          </template>
        </q-input>
      </template>
    </q-table>
  </q-page>
</template>

<script setup lang="ts">
import type { MeetingEvent } from "src/types/event";

import { useAsyncState } from "@vueuse/core";
import { api } from "boot/axios";
import { formatDate } from "src/intl";
import { computed, ref } from "vue";

const columns = [
  { field: "code", label: "Code", name: "code", sortable: true },
  { field: "title", label: "Title", name: "title", sortable: true },
  {
    field: (row: MeetingEvent) => formatDate(row.startDate),
    label: "Start date",
    name: "startDate",
    sortable: true,
  },
  { field: (row: MeetingEvent) => formatDate(row.endDate), label: "End date", name: "endDate", sortable: true },
  {
    field: (row: MeetingEvent) => row.venueCountry?.name ?? "",
    label: "Venue country",
    name: "venueCountry",
    sortable: true,
  },
  { field: "venueCity", label: "Venue city", name: "venueCity", sortable: true },
  { field: "dates", label: "Dates", name: "dates", sortable: true },
];
const { isLoading, state } = useAsyncState(async () => (await api.get("/events/")).data, []);
const search = ref("");

const events = computed(() => {
  const text = search.value.toLowerCase();
  return state.value.filter(
    (event: MeetingEvent) =>
      event.code.toLowerCase().includes(text) ||
      event.title.toLowerCase().includes(text) ||
      event.venueCity.toLowerCase().includes(text) ||
      event.venueCountry?.code.toLowerCase().includes(text) ||
      event.venueCountry?.name.toLowerCase().includes(text) ||
      event.venueCountry?.officialName.toLowerCase().includes(text),
  );
});
</script>
