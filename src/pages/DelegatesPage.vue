<template>
  <q-page class="q-pa-lg">
    <dsa-form
      v-if="selected"
      :model-value="true"
      :registration="selected"
      @hide="selected = null"
      @update="fetchData(false)"
    />
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
      @row-click="onRowClick"
    >
      <template #top>
        <div class="row justify-between full-width top-filters">
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
              @update:model-value="fetchData()"
            >
              <template #append>
                <q-icon name="search" />
              </template>
            </q-input>
            <code-scanner @code="setCode" />
          </div>
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
              :disable="disableEvent"
              popup-content-class="wrap-options"
              @update:model-value="fetchData()"
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
              style="max-width: 100px"
              @update:model-value="fetchData()"
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
              :disable="disablePaidDsa"
              @update:model-value="fetchData()"
            />
            <q-select
              v-model="status"
              dense
              filled
              name="status"
              :options="RegistrationStatusChoices"
              label="Status"
              clearable
              :disable="disableStatus"
              @update:model-value="fetchData()"
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
              :disable="disableTag"
              @update:model-value="fetchData()"
            />
          </div>
        </div>
      </template>

      <template #body-cell-passport="props">
        <q-td :props="props">
          <q-btn
            v-if="props.value"
            color="primary"
            dense
            flat
            :href="props.value.data"
            :download="props.value.filename"
            @click.stop
          >
            Passport
          </q-btn>
        </q-td>
      </template>
      <template #body-cell-boardingPass="props">
        <q-td :props="props">
          <q-btn
            v-if="props.value"
            color="primary"
            dense
            flat
            :href="props.value.data"
            :download="props.value.filename"
            @click.stop
          >
            Boarding
          </q-btn>
        </q-td>
      </template>
      <template #body-cell-signature="props">
        <q-td :props="props">
          <q-btn
            v-if="props.value"
            color="primary"
            dense
            flat
            :href="props.value.data"
            :download="props.value.filename"
            @click.stop
          >
            Signature
          </q-btn>
        </q-td>
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
import DsaForm from "components/dialogs/DsaForm.vue";
import { BooleanFilterChoices, RegistrationStatusChoices } from "src/constants";
import { formatDate } from "src/utils/intl";
import { useUserStore } from "stores/userStore";
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

type QTableRequestProps = Parameters<NonNullable<QTableProps["onRequest"]>>[0];

const tableRef = ref();
const route = useRoute();
const userStore = useUserStore();

defineProps({
  disableEvent: {
    default: false,
    type: Boolean,
  },
  disablePaidDsa: {
    default: false,
    type: Boolean,
  },
  disableStatus: {
    default: false,
    type: Boolean,
  },
  disableTag: {
    default: false,
    type: Boolean,
  },
});

const canEditDsa = computed(() => userStore.permissions.includes("events.change_dsa"));

const tag = useRouteQuery<string>("tag", "");
const status = useRouteQuery<string>("status", "");
const search = useRouteQuery<string>("search", "");
const paidDsa = useRouteQuery<string>("paidDsa", "");
const eventCode = useRouteQuery<string>("eventCode", "");
const priorityPassCode = useRouteQuery<string>("priorityPassCode", "");

const selected = ref<null | Registration>(null);

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
    field: (row) => row.dsa?.passport,
    label: "Passport",
    name: "passport",
  },
  {
    field: (row) => row.dsa?.boardingPass,
    label: "Boarding Pass",
    name: "boardingPass",
  },
  {
    field: (row) => row.dsa?.signature,
    label: "Signature",
    name: "signature",
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
      (c.name !== "tags" || !tag.value) &&
      (c.name !== "status" || !status.value) &&
      (c.name !== "paidDsa" || !paidDsa.value),
  ),
);

const { isLoading: isLoadingEvent, state: events } = useAsyncState(
  async () => (await api.get<MeetingEvent[]>("/events/?ordering=-startDate")).data,
  [],
);
const { isLoading: isLoadingTags, state: tags } = useAsyncState(
  async () => (await api.get<RegistrationTag[]>("/registration-tags/")).data,
  [],
);

watch([isLoadingEvent, route], () => {
  eventCode.value ||= events.value[0]?.code ?? "";
  if (eventCode.value) {
    fetchData();
  }
});

function fetchData(resetPagination = true) {
  if (resetPagination) {
    pagination.value.page = 1;
  }
  selected.value = null;
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

function onRowClick(event: Event, row: Registration) {
  if (canEditDsa.value) {
    selected.value = row;
  }
}

function setCode(code: string) {
  priorityPassCode.value = code;
  fetchData();
}
</script>

<style scoped lang="scss">
.top-filters {
  gap: 1rem;
}

.filter-list {
  display: flex;
  flex-wrap: wrap;
}

.filter-list > * {
  min-width: 150px;
  max-width: 350px;
}
</style>
