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
        :loading="isLoadingEvent"
      />
      <q-select
        v-model="region"
        dense
        filled
        name="region"
        :options="data?.regions"
        option-value="code"
        option-label="name"
        map-options
        emit-value
        label="Region"
        clearable
        :loading="isLoading"
      />

      <q-select
        v-model="status"
        dense
        filled
        name="status"
        :options="RegistrationStatusChoices"
        label="Status"
        clearable
        :loading="isLoading"
      />
    </div>
    <div v-if="data" class="q-mt-md">
      <div class="row wrap" style="height: 35rem; gap: 1rem">
        <q-card style="min-width: 30rem">
          <data-by-status :entries="entries" :statistics="data" />
        </q-card>
        <q-card style="min-width: 50rem">
          <data-by-organization-type :entries="entries" :statistics="data" />
        </q-card>
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
import DataByOrganizationType from "components/charts/DataByOrganizationType.vue";
import DataByStatus from "components/charts/DataByStatus.vue";
import { RegistrationStatusChoices } from "src/constants";
import { computed, ref, watch } from "vue";

const eventCode = useRouteQuery<string>("eventCode", "");
const { isLoading: isLoadingEvent, state: events } = useAsyncState(
  async () => (await api.get<MeetingEvent[]>("/events/?ordering=-startDate")).data,
  [],
);

const isLoading = ref(true);
const data = computedAsync(
  async () => (await api.get<Statistics>(`/events/${eventCode.value}/statistics/`)).data,
  null,
  isLoading,
);

watch([isLoadingEvent], () => {
  eventCode.value ||= events.value[0]?.code ?? "";
});

const status = useRouteQuery<string>("status", "");
const region = useRouteQuery<string>("region", "");

const entries = computed(
  () =>
    data.value?.registrations.filter(
      (r) => (!region.value || r.region === region.value) && (!status.value || r.status === status.value),
    ) ?? [],
);
</script>

<style scoped lang="scss">
.filter-list {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

.filter-list > * {
  min-width: 150px;
  max-width: 350px;
}
</style>
