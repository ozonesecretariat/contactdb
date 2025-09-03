<template>
  <q-card-section v-if="participant" class="col-grow">
    <p class="text-weight-medium">1. Review participant details below. Use the 'Edit' button to modify information:</p>
    <div v-if="errors.contact" class="text-negative">
      {{ errors.contact }}
    </div>
    <div class="bg-grey-2 rounded-borders">
      <participant-card
        v-if="invitation.participant"
        :participant="invitation.participant"
        :photo-url="invitation.getPhotoUrl(participant.id)"
      >
        <template #buttons>
          <q-btn :to="{ name: 'edit-participant', params: { participantId: participant.id } }" size="sm">Edit</q-btn>
        </template>
      </participant-card>
    </div>
  </q-card-section>
  <q-card-section v-if="participant" class="col-grow">
    <p class="text-weight-medium">
      2. Select the meetings for which you want to nominate the participant and their respective role
    </p>
    <div class="bg-grey-2 rounded-borders">
      <div v-for="event in invitation.events" :key="event.code" class="event q-pa-md">
        <div class="column">
          <div class="text-weight-medium">{{ event.code }} | {{ event.dates }}</div>
          <div class="q-mb-sm">{{ event.title }}</div>
          <q-slide-transition>
            <div v-show="nominationsToggle[event.code]">
              <q-select
                v-model="nominations[event.code]"
                :options="invitation.roles"
                label="Role of the participant"
                outlined
                dense
                class="role-select"
                :error="!!roleErrors[event.code]"
                :error-message="roleErrors[event.code]"
                hide-bottom-space
                :disable="nominationReadOnly(event)"
              />
            </div>
          </q-slide-transition>
        </div>
        <div class="column items-end">
          <q-toggle v-model="nominationsToggle[event.code]" :disable="nominationReadOnly(event)" />
          <p v-if="currentNominations[event.code]">
            {{ currentNominations[event.code]?.status }}
          </p>
        </div>
      </div>
    </div>
  </q-card-section>
  <q-card-section class="modal-footer">
    <q-btn :to="{ name: 'find-participant' }">Back</q-btn>
    <q-btn
      :color="hasChanges ? 'accent' : 'grey'"
      :disabled="!hasChanges"
      :loading="loading"
      @click="confirmNomination"
    >
      {{ hasChanges ? "Confirm nomination" : "No changes to save" }}
    </q-btn>
  </q-card-section>
  <q-dialog v-model="showConfirmDialog" persistent>
    <q-card>
      <q-card-section class="row items-center">
        <q-avatar icon="warning" color="negative" text-color="white" />
        <span class="q-ml-sm text-h6">Confirm Removal</span>
      </q-card-section>

      <q-card-section class="q-pt-none">
        <p>You are about to remove the nominations for the following event(s):</p>
        <ul>
          <li v-for="item in actionSummary.removing" :key="item.event.code">
            <strong>{{ item.event.code }}</strong>
            ({{ item.role }})
          </li>
        </ul>
      </q-card-section>

      <q-card-actions align="right">
        <q-btn v-close-popup flat label="Cancel" />
        <q-btn
          flat
          label="Remove nominations"
          color="negative"
          @click="
            performNomination();
            showConfirmDialog = false;
          "
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import type { MeetingEvent } from "src/types/event";
import type { EventNomination } from "src/types/nomination";

import { api } from "boot/axios";
import ParticipantCard from "components/ParticipantCard.vue";
import useFormErrors from "src/composables/useFormErrors";
import { useInvitationStore } from "stores/invitationStore";
import { computed, reactive, ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const loading = ref(false);
const invitation = useInvitationStore();
const participant = computed(() => invitation.participant);

const { errors, setErrors } = useFormErrors();
const nominations = reactive<Record<string, string>>({});
const nominationsToggle = reactive<Record<string, boolean>>({});
const roleErrors = reactive<Record<string, string>>({});
const currentNominations = computed(() => {
  const result: Record<string, EventNomination> = {};
  for (const nomination of invitation.nominations) {
    if (nomination.contact.id !== invitation.participant?.id) {
      continue;
    }
    result[nomination.event.code] = nomination;
  }
  return result;
});

const actionSummary = computed(() => {
  const removing = [];

  for (const event of invitation.events) {
    const isSelected = nominationsToggle[event.code];
    const currentNomination = currentNominations.value[event.code];
    const hasCurrentNomination = Boolean(currentNomination);

    // This allows us to keep tracks of whether any nomination are removed
    if (!isSelected && hasCurrentNomination) {
      removing.push({ event, role: currentNomination?.role });
    }
  }

  return { removing };
});

const hasChanges = computed(() => {
  // Check if current state differs from initial state
  for (const event of invitation.events) {
    const isSelected = nominationsToggle[event.code];
    const currentNomination = currentNominations.value[event.code];
    const hasCurrentNomination = Boolean(currentNomination);
    const selectedRole = nominations[event.code];

    if (isSelected !== hasCurrentNomination) {
      return true;
    }

    // Tracking role changes as well, not just selections
    if (isSelected && hasCurrentNomination && selectedRole !== currentNomination?.role) {
      return true;
    }
  }
  return false;
});

const willRemoveNominations = computed(() => actionSummary.value.removing.length > 0);

// Init values for all events
for (const event of invitation.events) {
  roleErrors[event.code] = "";
  nominations[event.code] = "";
  // If we only have one event, default to it being enabled
  nominationsToggle[event.code] = invitation.events.length === 1;
}

// Load current nominations for this participant
for (const [code, nomination] of Object.entries(currentNominations.value)) {
  nominations[code] = nomination.role;
  nominationsToggle[code] = Boolean(nomination.status);
}

const showConfirmDialog = ref(false);

async function confirmNomination() {
  if (!validateNominations()) {
    return;
  }

  // Show confirmation dialog if removing nominations
  if (willRemoveNominations.value) {
    showConfirmDialog.value = true;
    return;
  }

  await performNomination();
}

function nominationReadOnly(event: MeetingEvent) {
  return Boolean(currentNominations.value[event.code]) && currentNominations.value[event.code]?.status !== "Nominated";
}

async function performNomination() {
  const url = `/events-nominations/${invitation.token}/nominate-contact/${invitation.participantId}/`;

  loading.value = true;
  try {
    await api.post(
      url,
      Object.entries(nominations)
        .filter(([eventCode]) => nominationsToggle[eventCode])
        .map(([eventCode, role]) => ({
          contact: invitation.participantId,
          event: eventCode,
          role,
        })),
    );
    await invitation.loadNominations();
    await router.push({ name: "event-nominations" });
  } catch (e) {
    setErrors(e);
    throw e;
  } finally {
    loading.value = false;
  }
}

function validateNominations() {
  // Do not enable submit button when no changes have been performed
  if (!hasChanges.value) {
    return false;
  }

  let valid = true;
  for (const event of invitation.events) {
    if (!nominationsToggle[event.code]) {
      continue;
    }
    if (!nominations[event.code]) {
      roleErrors[event.code] = "Please select a role";
      valid = false;
    } else {
      roleErrors[event.code] = "";
    }
  }
  return valid;
}
</script>

<style scoped lang="scss">
.event {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: start;
}

.event + .event {
  border-top: 1px solid #ccc;
}

.role-select {
  width: 16rem;
}
</style>
