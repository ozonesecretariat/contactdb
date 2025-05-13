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
        <q-input v-model="search" borderless dense debounce="200" placeholder="Search" autofocus>
          <template #append>
            <q-icon name="search" />
          </template>
        </q-input>
      </template>
    </q-table>
  </q-page>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useAsyncState } from "@vueuse/core";
import { api } from "boot/axios";
import type { MeetingEvent } from "src/types/event";

const columns = [
  { name: "code", label: "Code", field: "code", sortable: true },
  { name: "title", label: "Title", field: "title", sortable: true },
  { name: "startDate", label: "Start date", field: "startDate", sortable: true },
  { name: "endDate", label: "End date", field: "endDate", sortable: true },
  { name: "venueCountry", label: "Venue country", field: (row: MeetingEvent) => row.venueCountry.name, sortable: true },
  { name: "venueCity", label: "Venue city", field: "venueCity", sortable: true },
  { name: "dates", label: "Dates", field: "dates", sortable: true },
];
const { state, isLoading } = useAsyncState(async () => (await api.get("/events/")).data, []);
const search = ref("");

const events = computed(() => {
  const text = search.value.toLowerCase();
  return state.value.filter(
    (event: MeetingEvent) =>
      event.code.toLowerCase().includes(text) ||
      event.title.toLowerCase().includes(text) ||
      event.venueCity.toLowerCase().includes(text) ||
      event.venueCountry.code.toLowerCase().includes(text) ||
      event.venueCountry.name.toLowerCase().includes(text) ||
      event.venueCountry.officialName.toLowerCase().includes(text),
  );
});
</script>
