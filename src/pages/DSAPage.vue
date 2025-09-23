<template>
  <q-page class="q-pa-lg">
    <q-table
      ref="tableRef"
      v-model:pagination="pagination"
      title="DSA"
      :rows="rows"
      :columns="filteredColumns"
      row-key="id"
      :loading="isLoading || isLoadingEvent || isLoadingTags"
      binary-state-sort
      :fullscreen="false"
      wrap-cells
      :rows-per-page-options="[5, 10, 20, 50]"
      @request="onRequest"
    >
      <template #top-left>
        <div class="q-gutter-md filter-list">
          <q-input
            v-model="search"
            dense
            filled
            debounce="300"
            placeholder="Search"
            name="search"
            autofocus
            role="search"
            label="Search"
            @update:model-value="fetchData"
          >
            <template #append>
              <q-icon name="search" />
            </template>
          </q-input>
          <code-scanner @code="setCode" />
        </div>
      </template>
      <template #top-right>
        <div class="q-gutter-md filter-list">
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
            @update:model-value="fetchData"
          />
          <q-select
            v-model="paidDsa"
            dense
            filled
            name="paidDsa"
            :options="BooleanFilterChoices"
            label="Paid DSA"
            map-options
            emit-value
            clearable
            @update:model-value="fetchData"
          />
          <q-input
            v-model="priorityPassCode"
            dense
            filled
            debounce="300"
            placeholder="Code"
            name="priorityPassCode"
            label="Code"
            clearable
            @update:model-value="fetchData"
          />
          <q-select
            v-model="status"
            dense
            filled
            name="status"
            :options="RegistrationStatusChoices"
            label="Status"
            clearable
            @update:model-value="fetchData"
          />
          <q-select
            v-model="tag"
            dense
            filled
            name="tag"
            :options="tags"
            option-value="name"
            option-label="name"
            map-options
            emit-value
            label="Tag"
            clearable
            placeholder="Tag"
            :loading="isLoadingTags"
            @update:model-value="fetchData"
          />
        </div>
      </template>
    </q-table>
  </q-page>
</template>

<script setup lang="ts">
import type { QTableColumn, QTableProps } from "quasar";
import type { MeetingEvent } from "src/types/event";
import type { Paginated } from "src/types/pagination";
import type { Registration, RegistrationTag } from "src/types/registration";

import { useAsyncState } from "@vueuse/core";
import { useRouteQuery } from "@vueuse/router";
import { api } from "boot/axios";
import CodeScanner from "components/dialogs/CodeScanner.vue";
import { BooleanFilterChoices, RegistrationStatusChoices } from "src/constants";
import { formatDate } from "src/utils/intl";
import { computed, ref, watch } from "vue";

type QTableRequestProps = Parameters<NonNullable<QTableProps["onRequest"]>>[0];

const tableRef = ref();

const { isLoading: isLoadingEvent, state: events } = useAsyncState(
  async () => (await api.get<MeetingEvent[]>("/events/?order_by=-start_date")).data,
  [],
);
const { isLoading: isLoadingTags, state: tags } = useAsyncState(
  async () => (await api.get<RegistrationTag[]>("/registration-tags/")).data,
  [],
);

const tag = useRouteQuery<string>("tag", "");
const status = useRouteQuery<string>("status", "");
const search = useRouteQuery<string>("search", "");
const paidDsa = useRouteQuery<string>("paidDsa", "");
const eventCode = useRouteQuery<string>("eventCode", "");
const priorityPassCode = useRouteQuery<string>("priorityPassCode", "");

const isLoading = ref(true);
const rows = ref<Registration[]>([]);
const pagination = ref({
  page: 1,
  rowsNumber: 0,
  rowsPerPage: 20,
});
const columns: QTableColumn<Registration>[] = [
  {
    field: (row) => row.dsaCountry?.name,
    label: "Country",
    name: "country",
  },
  {
    field: (row) => row.contact.title,
    label: "Title",
    name: "title",
  },
  {
    field: (row) => row.contact.firstName,
    label: "First Name",
    name: "firstName",
  },
  {
    field: (row) => row.contact.lastName,
    label: "Last Name",
    name: "lastName",
  },
  {
    field: (row) => row.dsa?.umojaTravel,
    label: "Umoja Travel #",
    name: "umojaTravel",
  },
  {
    field: (row) => row.dsa?.bp,
    label: "BP #",
    name: "bp",
  },
  {
    field: (row) => formatDate(row.dsa?.arrivalDate),
    label: "Arrival date",
    name: "arrivalDate",
  },
  {
    field: (row) => formatDate(row.dsa?.departureDate),
    label: "Departure date",
    name: "departureDate",
  },
  {
    field: (row) => row.dsa?.numberOfDays,
    label: "N° of days",
    name: "numberOfDays",
  },
  {
    field: (row) => row.dsa?.dsaOnArrival,
    label: "100% of DSA on arrival date in USD",
    name: "dsaOnArrival",
  },
  {
    field: (row) => row.event.termExp,
    label: "Term. Exp. In USD",
    name: "termExp",
  },
  {
    field: (row) => row.dsa?.totalDsa,
    label: "Total DSA in USD",
    name: "totalDsa",
  },
  {
    field: (row) => row.dsa?.cashCard,
    label: "Cash Card",
    name: "cashCard",
  },
  {
    field: (row) => (row.dsa?.paidDsa ? "Yes" : "No"),
    label: "Paid DSA",
    name: "paidDsa",
  },
  {
    field: (row) => row.status,
    label: "Status",
    name: "status",
  },
  {
    field: (row) => row.tags.join(", "),
    label: "Tags",
    name: "tags",
  },
];
const filteredColumns = computed(() =>
  columns.filter(
    (c) =>
      (c.name !== "status" || !status.value) &&
      (c.name !== "tags" || !tag.value) &&
      (c.name !== "paidDsa" || !paidDsa.value),
  ),
);

function fetchData() {
  tableRef.value.requestServerInteraction();
}

async function onRequest(props: QTableRequestProps) {
  const { page, rowsPerPage: pageSize } = props.pagination;

  isLoading.value = true;
  try {
    const resp = await api.get<Paginated<Registration>>("/registrations/", {
      params: {
        eventCode: eventCode.value,
        page,
        pageSize,
        paidDsa: paidDsa.value,
        priorityPassCode: priorityPassCode.value,
        search: search.value,
        status: status.value,
        tag: tag.value,
      },
    });
    const data = resp.data;

    rows.value.splice(0, rows.value.length, ...data.results);
    pagination.value.page = page;
    pagination.value.rowsNumber = data.count;
    pagination.value.rowsPerPage = pageSize;
  } finally {
    isLoading.value = false;
  }
}

function setCode(code: string) {
  priorityPassCode.value = code;
  fetchData();
}

watch(isLoadingEvent, () => {
  eventCode.value ||= events.value[0]?.code ?? "";
  fetchData();
});
</script>

<style scoped lang="scss">
.filter-list {
  display: flex;
}

.filter-list > * {
  min-width: 150px;
}
</style>
