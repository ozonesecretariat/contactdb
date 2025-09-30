<template>
  <q-page class="q-pa-lg">
    <div class="filter-list">
      <q-select
        v-model="eventCode"
        dense
        filled
        name="eventCode"
        :options="events"
        option-value="code"
        option-label="title"
        map-options
        emit-value
        label="Event"
        popup-content-class="wrap-options"
        :loading="isLoadingEvent"
      />
      <q-select
        v-model="group"
        dense
        filled
        name="disc"
        :options="groupChoices"
        map-options
        emit-value
        label="Group by"
        :loading="isLoading"
      />
      <q-select
        v-model="status"
        dense
        filled
        name="status"
        :options="data?.schema.status ?? []"
        label="Status"
        clearable
        :loading="isLoading"
      />
    </div>
    <div v-if="filteredData && dataByRegion" class="q-mt-md dashboard">
      <div class="row">
        <pie-chart :key1="group" title="Total Participants" :stats="filteredData" class="col-4" />
        <bar-chart
          title="Participants by Organization Type"
          :horizontal="true"
          :key1="group"
          key2="organizationType"
          :stack="true"
          :stats="filteredData"
          class="col"
        />
      </div>
      <div class="row">
        <bar-chart
          title="Participants by Region"
          :horizontal="false"
          :key1="group"
          key2="region"
          :stack="false"
          :stats="filteredData"
          class="col-4"
        />
        <bar-chart
          v-for="(stats, region) in dataByRegion ?? {}"
          :key="region"
          :title="`${region} Participants`"
          :horizontal="true"
          :key1="group"
          key2="subregion"
          :stack="true"
          :stats="stats"
          class="col"
        />
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import type { MeetingEvent } from "src/types/event";
import type { Statistics } from "src/types/statistics";

import { computedAsync, useAsyncState } from "@vueuse/core";
import { useRouteQuery } from "@vueuse/router";
import { api } from "boot/axios";
import BarChart from "components/charts/BarChart.vue";
import PieChart from "components/charts/PieChart.vue";
import { computed, ref, watch } from "vue";

const eventCode = useRouteQuery<string>("eventCode", "");
const { isLoading: isLoadingEvent, state: events } = useAsyncState(
  async () => (await api.get<MeetingEvent[]>("/events/?ordering=-startDate")).data,
  [],
);

const groupChoices = [
  { label: "Status", value: "status" },
  { label: "Role", value: "role" },
  { label: "Gender", value: "gender" },
] as const;
type GroupChoice = (typeof groupChoices)[number]["value"];

const group = useRouteQuery<GroupChoice>("group", "status");
const status = useRouteQuery<string>("status", "");

const isLoading = ref(true);
const data = computedAsync(
  async () => (await api.get<Statistics>(`/events/${eventCode.value}/statistics/`)).data,
  null,
  isLoading,
);

watch([isLoadingEvent], () => {
  eventCode.value ||= events.value[0]?.code ?? "";
});

const filteredData = computed<null | Statistics>(() => {
  if (!data.value) return null;
  return {
    ...data.value,
    registrations: data.value.registrations.filter((r) => !status.value || r.status === status.value),
  };
});

const dataByRegion = computed<null | Record<string, Statistics>>(() => {
  const stats = filteredData.value;
  if (!stats) return null;

  const result: Record<string, Statistics> = {};
  for (const region of stats.schema.region) {
    const registrations = stats.registrations.filter((r) => r.region === region);
    const subregions = new Set(registrations.map((r) => r.subregion));
    result[region] = {
      registrations,
      schema: {
        ...stats.schema,
        subregion: stats.schema.subregion.filter((name) => subregions.has(name)),
      },
    };
  }
  return result;
});
</script>

<style scoped lang="scss">
.filter-list {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

.filter-list > * {
  min-width: 150px;
  max-width: 450px;
}

.dashboard {
  .row {
    gap: 1rem;
    flex-wrap: wrap;
  }

  .row + .row {
    margin-top: 1rem;
  }

  .row > * {
    height: 35rem;
  }
}
</style>
