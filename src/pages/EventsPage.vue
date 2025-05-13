<template>
  <q-page class="row items-center justify-evenly">
    <q-table
      :rows="events"
      :loading="isLoading"
      :columns="columns"
      :pagination="{
        rowsPerPage: 15,
        sortBy: 'code',
        descending: false,
      }"
    />
  </q-page>
</template>

<script setup lang="ts">
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
const { state: events, isLoading } = useAsyncState(async () => (await api.get("/events/")).data, []);
</script>
