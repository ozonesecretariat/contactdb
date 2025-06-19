<template>
  <q-card-section v-if="participant" class="col-grow">
    <p class="text-weight-medium">1. Review participant details below. Use the 'Edit' button to modify information:</p>
    <div class="bg-grey-2 q-pa-md rounded-borders">
      <div class="row items-start justify-between">
        <div>
          <p class="text-h6 text-secondary">
            {{ participant?.fullName }}
          </p>
          <p class="text-subtitle1">
            {{ participant.designation }}
          </p>
        </div>
        <q-btn :to="{ name: 'edit-participant', params: { participantId: participant.id } }" size="sm">Edit</q-btn>
      </div>
      <p class="text-h6">
        {{ participant.organization?.name }}
      </p>
      <div class="row items-start justify-between">
        <div v-if="organization">
          {{ organization.country?.name ?? organization.government?.name }}
          {{ organization.state }}
          {{ organization.postalCode }}
          <br />
          {{ organization.address }}
        </div>
        <div>
          Email: {{ participant.emails?.[0] ?? "-" }}
          <br />
          Mobile: {{ participant.mobiles?.[0] ?? "-" }}
        </div>
      </div>
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
              />
            </div>
          </q-slide-transition>
        </div>
        <q-toggle v-model="nominationsToggle[event.code]" />
      </div>
    </div>
  </q-card-section>
  <q-card-section class="modal-footer">
    <q-btn :to="{ name: 'find-participant' }">Back</q-btn>
    <q-btn color="accent" :loading="loading" @click="confirmNomination">Confirm nomination</q-btn>
  </q-card-section>
</template>

<script setup lang="ts">
import { useStorage } from "@vueuse/core";
import { api } from "boot/axios";
import { useInvitationStore } from "stores/invitationStore";
import { computed, reactive, ref } from "vue";
import { useRouter } from "vue-router";

const dontShowNominationConfirmation = useStorage("dontShowNominationConfirmation", false);
const router = useRouter();
const loading = ref(false);
const invitation = useInvitationStore();
const participant = computed(() => invitation.participant);
const organization = computed(() => invitation.participant?.organization);

const nominations = reactive<Record<string, string>>({});
const nominationsToggle = reactive<Record<string, boolean>>({});
const roleErrors = reactive<Record<string, string>>({});

for (const event of invitation.events) {
  roleErrors[event.code] = "";
  nominations[event.code] = "";
  nominationsToggle[event.code] = false;
}

// Load current nominations for this participant
for (const nomination of invitation.nominations) {
  if (nomination.contact.id !== invitation.participant?.id) {
    continue;
  }
  nominations[nomination.event.code] = nomination.role;
  nominationsToggle[nomination.event.code] = Boolean(nomination.status);
}

async function confirmNomination() {
  if (!validateNominations()) {
    return;
  }

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
    if (dontShowNominationConfirmation.value) {
      await router.push({ name: "event-nominations" });
    } else {
      await router.push({ name: "confirm-nomination" });
    }
  } finally {
    loading.value = false;
  }
}

function validateNominations() {
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
