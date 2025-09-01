<template>
  <q-page class="q-pa-md">
    <code-scanner ref="codeScannerRef" @code="setCode" />
    <take-photo ref="takePhotoRef" @capture="setPicture" />
    <search-pass ref="searchPassRef" @code="setCode" />

    <p class="text-grey">Scan QR or enter code</p>
    <section class="flex items-center justify-between q-col-gutter-md">
      <div class="flex q-gutter-md items-center">
        <q-btn label="Scan code" color="secondary" icon="qr_code_scanner" @click="codeScannerRef?.show()" />
        <q-btn color="primary" label="Search for pass" icon="search" @click="searchPassRef?.show()" />
      </div>
      <div class="flex q-gutter-md items-center">
        <q-input v-model="passCode" label="Code" filled autofocus dense name="code" />
        <q-btn
          label="Verify"
          color="positive"
          icon="how_to_reg"
          :loading="loading"
          :disable="passCode.length < 10"
          @click="loadPriorityPass()"
        />
      </div>
    </section>
    <div v-if="pass" class="pass-container">
      <section class="contact-section q-mt-lg">
        <q-card flat bordered class="contact-card">
          <participant-card v-if="pass.contact" :participant="pass.contact" :photo-url="photoUrl" />

          <q-separator />

          <q-card-actions v-if="canViewRegistration || canEditContact">
            <q-btn v-if="canViewRegistration" color="positive" icon="picture_as_pdf" :href="badgeUrl" target="_blank">
              Print badge
            </q-btn>
            <q-btn v-if="canEditContact" color="primary" icon="photo_camera" @click="takePhotoRef?.show()">
              Take photo
            </q-btn>
          </q-card-actions>
        </q-card>
        <div class="registrations-section q-pt-lg text-subtitle1 text-white">
          <q-card v-if="validRange" flat bordered class="valid-card bg-positive">Registered {{ validRange }}</q-card>
          <q-card v-else flat bordered class="valid-card bg-negative">Not registered</q-card>
        </div>
      </section>
      <div v-if="canViewRegistration" class="registrations-section">
        <section v-for="registration in registrations" :key="registration.id" class="q-mt-lg">
          <q-card flat bordered class="event-card" :class="cardColors[registration.status]">
            <q-card-section>
              <div class="text-overline flex justify-between">
                <span>
                  {{ registration.event.code }} | {{ registration.event.venueCity }} |
                  {{ registration.event.venueCountry?.name }} | {{ registration.event.dates }}
                </span>
                <q-chip>
                  <q-avatar floating :icon="statusIcons[registration.status]" />
                  {{ registration.status }}
                </q-chip>
              </div>
            </q-card-section>
            <q-separator />
            <q-card-section>
              <div class="text-h5">
                {{ registration.event.title }}
              </div>
              <div class="text-caption">
                {{ registration.role }}
              </div>
            </q-card-section>
            <q-separator v-if="canEditRegistration" />
            <q-card-actions v-if="canEditRegistration" align="right">
              <q-btn
                v-if="registration.status !== 'Registered'"
                color="positive"
                label="Register"
                @click="updateRegistrationStatus(registration, 'Registered')"
              />
              <q-btn
                v-if="registration.status !== 'Revoked'"
                color="negative"
                label="Revoke"
                @click="updateRegistrationStatus(registration, 'Revoked')"
              />
            </q-card-actions>
          </q-card>
        </section>
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import type { AxiosError } from "axios";
import type { PriorityPass } from "src/types/priorityPass";
import type { Registration } from "src/types/registration";

import { useRouteQuery } from "@vueuse/router";
import { api, apiBase, apiURL } from "boot/axios";
import CodeScanner from "components/CodeScanner.vue";
import ParticipantCard from "components/ParticipantCard.vue";
import SearchPass from "components/SearchPass.vue";
import TakePhoto from "components/TakePhoto.vue";
import { useQuasar } from "quasar";
import { useUserStore } from "stores/userStore";
import { computed, onMounted, ref, useTemplateRef } from "vue";

const $q = useQuasar();
const userStore = useUserStore();

const takePhotoRef = useTemplateRef("takePhotoRef");
const codeScannerRef = useTemplateRef("codeScannerRef");
const searchPassRef = useTemplateRef("searchPassRef");

const passCode = useRouteQuery<string>("code", "");
const pass = ref<null | PriorityPass>(null);
const loading = ref(false);
// Not really here for security reasons, just to decide when to show a more compact view.
// Only users that can view the priority pass can get to this page anyway.
const canViewRegistration = computed(() => userStore.permissions.includes("events.view_registration"));
// Check who has edit permissions
const canEditContact = computed(() => userStore.permissions.includes("core.change_contact"));
const canEditRegistration = computed(() => userStore.permissions.includes("events.change_registration"));
const registrations = computed(() =>
  [...(pass.value?.registrations ?? [])].sort((a, b) => (a.event.code > b.event.code ? 1 : -1)),
);
const validRange = computed(() => pass?.value?.validDateRange);

const badgeUrl = computed(() => {
  if (!pass?.value?.badgeUrl) return "";

  return apiBase + pass.value.badgeUrl;
});
const photoUrl = computed(() => {
  if (!pass?.value?.contact?.hasPhoto) return "";

  return `${apiURL}/contacts/${pass.value?.contact.id}/photo/`;
});

const cardColors = {
  Accredited: "bg-primary",
  Nominated: "bg-info",
  Registered: "bg-positive",
  Revoked: "bg-negative",
};
const statusIcons = {
  Accredited: "verified",
  Nominated: "question_mark",
  Registered: "how_to_reg",
  Revoked: "block",
};

onMounted(() => {
  if (passCode.value) {
    loadPriorityPass();
  }
});

async function loadPriorityPass() {
  pass.value = null;
  loading.value = true;
  try {
    pass.value = (await api.get<PriorityPass>(`/priority-passes/${passCode.value}/`)).data;
  } catch (e) {
    switch ((e as AxiosError).status) {
      case 404:
        $q.notify({
          message: "Invalid code!",
          type: "negative",
        });
        break;
      default:
        $q.notify({
          message: "Could not verify code due to unknown error, please try again later!",
          type: "negative",
        });
        throw e;
    }
  } finally {
    loading.value = false;
  }
}

function setCode(code: string) {
  passCode.value = code;
  loadPriorityPass();
}

async function setPicture(photo: string) {
  if (!pass.value?.contact) return;

  loading.value = true;
  try {
    await api.patch(`/contacts/${pass.value.contact.id}/`, {
      photo,
    });
    await loadPriorityPass();
  } catch (e) {
    $q.notify({
      message: "Could not update contact photo, please try again later!",
      type: "negative",
    });
    throw e;
  } finally {
    loading.value = false;
  }
}

async function updateRegistrationStatus(registration: Registration, newStatus: Registration["status"]) {
  loading.value = true;
  try {
    await api.patch(`/registration-status/${registration.id}/`, {
      status: newStatus,
    });
    $q.notify({
      message: "Registration status updated.",
      type: "positive",
    });
    await loadPriorityPass();
  } catch (e) {
    $q.notify({
      message: "Could not update registration status, please try again later!",
      type: "negative",
    });
    throw e;
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped lang="scss">
.pass-container {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 2rem;
  max-width: 125rem;
}

.registrations-section,
.contact-section {
  flex-grow: 1;
}

.contact-card,
.event-card,
.valid-card {
  max-width: 40rem;
}

.valid-card {
  padding: 0.25rem 1rem;
}

@media (min-width: 2000px) {
  .contact-card,
  .event-card,
  .valid-card {
    max-width: 50rem;
  }
}

.contact-photo {
  max-width: 20rem;
  max-height: 20rem;
}

.contact-photo img {
  max-width: 100%;
  max-height: 100%;
}
</style>
