<template>
  <q-card-section>
    <p class="text-subtitle1">Find participant</p>
    <div class="flex q-gutter-md">
      <q-input
        v-model="search"
        placeholder="Enter name or email address"
        autofocus
        role="search"
        outlined
        dense
        class="col-grow"
      >
        <template #prepend>
          <q-icon name="search" />
        </template>
      </q-input>
      <q-btn icon="person_add" :to="{ name: 'create-participant' }">Create new</q-btn>
    </div>
  </q-card-section>

  <q-card-section class="col-grow participant-section">
    <q-table
      :rows="filteredParticipants"
      :columns="columns"
      row-key="id"
      :loading="!invitation.initialized"
      :pagination="{
        rowsPerPage: 5,
        sortBy: 'fullName',
        descending: false,
      }"
      :dense="$q.screen.lt.lg"
      :grid="$q.screen.lt.md"
      @row-click="handleRowClick"
    >
      <template #body-cell-emails="props">
        <q-td :props="props">
          <ul class="no-list q-pl-none">
            <li v-for="email in props.row.emails" :key="email">
              {{ email }}
            </li>
          </ul>
        </q-td>
      </template>
      <template #body-cell-actions="props">
        <q-td :props="props">
          <q-btn
            size="sm"
            :to="{ name: 'nominate-participant', params: { participantId: props.row.id } }"
            color="accent"
          >
            Select
          </q-btn>
        </q-td>
      </template>
    </q-table>
  </q-card-section>

  <q-card-section class="modal-footer">
    <q-btn :to="{ name: 'event-nominations' }">Close</q-btn>
  </q-card-section>
</template>

<script setup lang="ts">
import type { Contact } from "src/types/nomination";

import { useRouteQuery } from "@vueuse/router";
import { type QTableColumn, useQuasar } from "quasar";
import { unaccentSearch } from "src/utils/search";
import { useInvitationStore } from "stores/invitationStore";
import { computed } from "vue";
import { useRouter } from "vue-router";

const $q = useQuasar();
const router = useRouter();
const search = useRouteQuery("searchParticipant", "");
const invitation = useInvitationStore();

const filteredParticipants = computed(() =>
  unaccentSearch(search.value, invitation.contacts, (row) => [
    row.firstName,
    row.lastName,
    row.fullName,
    ...row.emails,
    row.organization?.name,
  ]),
);

const columns = computed(() => {
  const result: QTableColumn<Contact>[] = [
    {
      align: "left",
      field: (row) => row.fullName,
      label: "Full Name",
      name: "fullName",
      sortable: true,
    },
    {
      align: "left",
      field: (row) => row.emails.join(", "),
      label: "Emails",
      name: "emails",
      sortable: true,
    },
    {
      align: "left",
      field: (row) => row.organization?.name ?? "-",
      label: "Organization",
      name: "organization",
      sortable: true,
    },
  ];

  if (!$q.screen.lt.md) {
    result.push({
      align: "right",
      field: () => "",
      label: "Actions",
      name: "actions",
      sortable: false,
    });
  }

  return result;
});

function handleRowClick(ev: Event, row: Contact) {
  if ($q.screen.lt.md) {
    router.push({ name: "nominate-participant", params: { participantId: row.id } });
  }
}
</script>

<style scoped lang="scss">
.participant-section {
  min-height: 30rem;
}
</style>
