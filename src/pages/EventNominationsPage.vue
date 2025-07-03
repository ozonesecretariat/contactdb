<template>
  <div class="flex column q-gutter-y-md">
    <div class="text-subtitle2">Ozone Secretariat</div>
    <div class="flex q-gutter-md">
      <q-input v-model="search" placeholder="Search" autofocus role="search" filled dense class="col-grow">
        <template #prepend>
          <q-icon name="search" />
        </template>
      </q-input>
      <add-nomination />
    </div>
    <div class="text-subtitle2 q-mt-xl">Current nominations</div>
    <q-table
      :rows="filteredNominations"
      :columns="columns"
      row-key="id"
      :loading="!invitation.initialized"
      :pagination="{
        rowsPerPage: 15,
        sortBy: 'fullName',
        descending: false,
      }"
      :dense="$q.screen.lt.lg"
      :grid="$q.screen.lt.md"
      @row-click="handleRowClick"
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
          <q-btn
            icon="edit"
            flat
            size="sm"
            round
            aria-label="Edit"
            :to="{ name: 'nominate-participant', params: { participantId: props.row.contact.id } }"
          />
        </q-td>
      </template>
    </q-table>
  </div>
</template>

<script setup lang="ts">
import type { Contact, EventNomination } from "src/types/nomination";
import type { QTableColumnWithTooltip } from "src/types/quasar";

import { useRouteQuery } from "@vueuse/router";
import AddNomination from "components/nominations/AddNomination.vue";
import { useQuasar } from "quasar";
import { unaccentSearch } from "src/utils/search";
import { useInvitationStore } from "stores/invitationStore";
import { computed } from "vue";
import { useRouter } from "vue-router";

interface GroupedEventNomination {
  contact: Contact;
  nominations: {
    [key: string]: EventNomination;
  };
}

const $q = useQuasar();
const router = useRouter();
const search = useRouteQuery("search", "");
const invitation = useInvitationStore();
invitation.load();

const groupedNominations = computed(() => {
  const result: Record<number, GroupedEventNomination> = {};
  for (const nomination of invitation.nominations) {
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
  for (const event of invitation.events) {
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
    item.contact.emails,
  ]),
);

function handleRowClick(ev: Event, row: GroupedEventNomination) {
  if ($q.screen.lt.md) {
    router.push({ name: "nominate-participant", params: { participantId: row.contact.id } });
  }
}
</script>
