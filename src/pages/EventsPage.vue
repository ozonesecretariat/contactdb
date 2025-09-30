<template>
  <q-page class="q-pa-lg">
    <q-table
      :rows="events"
      :loading="isLoading"
      :columns="columns"
      :pagination="{
        rowsPerPage: 15,
        sortBy: 'startDate',
        descending: true,
      }"
    >
      <template #top-left>Events</template>
      <template #top-right>
        <q-input v-model="search" borderless dense placeholder="Search" autofocus role="search">
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
import { useRouteQuery } from "@vueuse/router";
import { api } from "boot/axios";
import { formatDate } from "src/utils/intl";
import { unaccentSearch } from "src/utils/search";
import { computed } from "vue";

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
const { isLoading, state } = useAsyncState(
  async () =>
    (
      await api.get<MeetingEvent[]>("/events/", {
        params: {
          isCurrent: true,
        },
      })
    ).data,
  [],
);
const search = useRouteQuery("search", "");

const events = computed(() =>
  unaccentSearch(search.value, state.value, (event) => [
    event.code,
    event.title,
    event.venueCity,
    event.venueCountry?.code,
    event.venueCountry?.name,
    event.venueCountry?.officialName,
  ]),
);
</script>
