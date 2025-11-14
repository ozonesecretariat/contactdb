<template>
  <q-page class="q-pa-lg">
    <dsa-form
      v-if="selected && tags"
      :model-value="true"
      :registration="selected"
      :possible-tags="tags.map((t) => t.name)"
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
            >
              <template #append>
                <q-icon name="search" />
              </template>
            </q-input>
            <code-scanner @code="setCode" />
            <q-btn label="Download report" color="primary" icon="download" :href="downloadReportLink" download />
            <q-btn label="Download files" color="primary" icon="download" :href="downloadFilesLink" download />
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
            />
            <q-select
              v-model="status"
              dense
              filled
              multiple
              use-chips
              stack-label
              name="status"
              :options="RegistrationStatusChoices"
              label="Status"
              :disable="disableStatus"
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
            />
          </div>
        </div>
      </template>

      <template #body-cell-passport="cellProps">
        <q-td :props="cellProps">
          <q-btn
            v-if="cellProps.value"
            color="primary"
            dense
            flat
            :href="cellProps.value.data"
            :download="cellProps.value.filename"
            @click.stop
          >
            Passport
          </q-btn>
        </q-td>
      </template>
      <template #body-cell-boardingPass="cellProps">
        <q-td :props="cellProps">
          <q-btn
            v-if="cellProps.value"
            color="primary"
            dense
            flat
            :href="cellProps.value.data"
            :download="cellProps.value.filename"
            @click.stop
          >
            Boarding
          </q-btn>
        </q-td>
      </template>
      <template #body-cell-signature="cellProps">
        <q-td :props="cellProps">
          <q-btn
            v-if="cellProps.value"
            color="primary"
            dense
            flat
            :href="cellProps.value.data"
            :download="cellProps.value.filename"
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
import { computed, type PropType, ref, watch } from "vue";
import { useRoute } from "vue-router";

type QTableRequestProps = Parameters<NonNullable<QTableProps["onRequest"]>>[0];

const tableRef = ref();
const route = useRoute();
const userStore = useUserStore();

const props = defineProps({
  columns: {
    default: null,
    type: Array as PropType<string[]>,
  },
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
const status = useRouteQuery<string[]>("status", [], { transform: (val) => (Array.isArray(val) ? val : [val]) });
const search = useRouteQuery<string>("search", "");
const paidDsa = useRouteQuery<string>("paidDsa", "");
const eventCode = useRouteQuery<string>("eventCode", "");
const priorityPassCode = useRouteQuery<string>("priorityPassCode", "");

const selected = ref<null | Registration>(null);

const isLoading = ref(false);
const rows = ref<Registration[]>([]);
const pagination = ref({
  page: 1,
  rowsNumber: 0,
  rowsPerPage: 20,
});
const possibleColumns: QTableColumn<Registration>[] = [
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
  possibleColumns.filter(
    (c) =>
      (!props.columns || props.columns.includes(c.name)) &&
      (c.name !== "tags" || !tag.value) &&
      (c.name !== "status" || !status.value) &&
      (c.name !== "paidDsa" || !paidDsa.value),
  ),
);
const downloadReportLink = computed(() => buildDownloadUrl("/registrations/export_dsa/"));
const downloadFilesLink = computed(() => buildDownloadUrl(`/registrations/export_dsa_files/`));

const { isLoading: isLoadingEvent, state: events } = useAsyncState(
  async () =>
    (
      await api.get<MeetingEvent[]>("/events/", {
        params: {
          isRecent: true,
          ordering: "-startDate",
        },
      })
    ).data,
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

const apiFilterParams = computed(() => ({
  eventCode: eventCode.value,
  paidDsa: paidDsa.value,
  priorityPassCode: priorityPassCode.value,
  search: search.value,
  status: status.value.join(","),
  tag: tag.value,
}));

function buildDownloadUrl(url: string) {
  return api.getUri({ params: apiFilterParams.value, url });
}

function fetchData(resetPagination = true) {
  if (resetPagination) {
    pagination.value.page = 1;
  }
  selected.value = null;
  tableRef.value.requestServerInteraction();
}

async function onRequest(requestProps: QTableRequestProps) {
  const { page, rowsPerPage: pageSize } = requestProps.pagination;

  isLoading.value = true;
  try {
    const resp = await api.get<Paginated<Registration>>("/registrations/", {
      params: {
        ...apiFilterParams.value,
        page,
        pageSize,
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
  align-items: start;
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
