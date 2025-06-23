<template>
  <q-card-section class="col-grow column">
    <div class="flex q-gutter-md">
      <q-input
        v-model="data.title"
        :error="!!errors.title"
        :error-message="errors.title"
        outlined
        label="Title"
        name="title"
        class="small-input"
      />
      <q-input
        v-model="data.firstName"
        :error="!!errors.firstName"
        :error-message="errors.firstName"
        outlined
        label="First Name"
        name="firstName"
      />
      <q-input
        v-model="data.lastName"
        :error="!!errors.lastName"
        :error-message="errors.lastName"
        outlined
        label="Last Name"
        name="lastName"
      />
    </div>
    <q-select
      v-model="data.organization"
      outlined
      label="Organization"
      name="organization"
      :error="!!errors.organization"
      :error-message="errors.organization"
      :options="invitation.organizations"
      option-value="id"
      option-label="name"
      map-options
      emit-value
    />
    <q-input
      v-model="data.designation"
      :error="!!errors.designation"
      :error-message="errors.designation"
      outlined
      label="Designation"
      name="designation"
    />
    <q-input
      v-model="data.department"
      :error="!!errors.department"
      :error-message="errors.department"
      outlined
      label="Department"
      name="department"
    />
    <q-input
      v-model="data.emails"
      :error="!!errors.emails"
      :error-message="errors.emails"
      outlined
      label="Email"
      name="emails"
    >
      <template #prepend>
        <q-icon name="email" />
      </template>
    </q-input>
    <q-input
      v-model="data.mobiles"
      :error="!!errors.mobiles"
      :error-message="errors.mobiles"
      outlined
      label="Mobile"
      name="mobiles"
    />
    <q-input
      v-model="data.emailCcs"
      :error="!!errors.emailCcs"
      :error-message="errors.emailCcs"
      outlined
      label="Secondary Email"
      name="emailCcs"
    >
      <template #prepend>
        <q-icon name="email" />
      </template>
    </q-input>
    <q-input
      v-model="data.phones"
      :error="!!errors.phones"
      :error-message="errors.phones"
      outlined
      label="Phone"
      name="phones"
    />
    <q-checkbox
      v-model="data.hasCredentials"
      :error="!!errors.hasCredentials"
      :error-message="errors.hasCredentials"
      label="Credentials"
    />
    <div v-if="data.hasCredentials">
      <q-file
        v-model="data.credentials"
        :error="!!errors.credentials"
        :error-message="errors.credentials"
        label="Credentials"
        outlined
        accept=".pdf,.doc,.docx"
        hint="Upload pdf or doc file"
      >
        <template #append>
          <q-icon name="attach_file" />
        </template>
      </q-file>
    </div>
    <q-checkbox
      v-model="data.needsVisaLetter"
      :error="!!errors.needsVisaLetter"
      :error-message="errors.needsVisaLetter"
      label="Needs visa letter"
    />
    <div v-if="data.needsVisaLetter">
      <div class="row full-width">
        <q-input
          v-model="data.passportNumber"
          :error="!!errors.passportNumber"
          :error-message="errors.passportNumber"
          label="Passport number"
          outlined
          class="col"
        />
        <q-input
          v-model="data.nationality"
          :error="!!errors.nationality"
          :error-message="errors.nationality"
          label="Nationality"
          outlined
          class="col q-ml-md"
        />
      </div>
      <div class="row full-width">
        <q-input
          v-model="data.passportDateOfIssue"
          :error="!!errors.passportDateOfIssue"
          :error-message="errors.passportDateOfIssue"
          outlined
          mask="####-##-##"
          :rules="['date']"
          label="Date of Issue"
          class="col"
        >
          <template #append>
            <q-icon name="event" class="cursor-pointer">
              <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                <q-date v-model="data.passportDateOfIssue" mask="YYYY-MM-DD">
                  <div class="row items-center justify-end">
                    <q-btn v-close-popup label="Close" color="primary" flat />
                  </div>
                </q-date>
              </q-popup-proxy>
            </q-icon>
          </template>
        </q-input>
        <q-input
          v-model="data.passportDateOfExpiry"
          :error="!!errors.passportDateOfExpiry"
          :error-message="errors.passportDateOfExpiry"
          outlined
          mask="####-##-##"
          :rules="['date']"
          label="Date of Expiry"
          class="col q-ml-md"
        >
          <template #append>
            <q-icon name="event" class="cursor-pointer">
              <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                <q-date v-model="data.passportDateOfExpiry" mask="YYYY-MM-DD">
                  <div class="row items-center justify-end">
                    <q-btn v-close-popup label="Close" color="primary" flat />
                  </div>
                </q-date>
              </q-popup-proxy>
            </q-icon>
          </template>
        </q-input>
      </div>
      <q-file
        v-model="data.passport"
        :error="!!errors.passport"
        :error-message="errors.passport"
        label="Passport"
        outlined
        accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
        hint="Upload pdf, doc or image file"
      >
        <template #append>
          <q-icon name="attach_file" />
        </template>
      </q-file>
    </div>
  </q-card-section>
  <q-card-section class="modal-footer">
    <q-btn :to="{ name: 'find-participant' }">Cancel</q-btn>
    <q-btn color="accent" :loading="loading" @click="saveForm">Save</q-btn>
  </q-card-section>
</template>

<script setup lang="ts">
import type { Contact } from "src/types/registration";

import { api } from "boot/axios";
import useFormErrors from "src/composables/useFormErrors";
import { useInvitationStore } from "stores/invitationStore";
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";

const loading = ref(false);
const invitation = useInvitationStore();
const router = useRouter();
const { errors, setErrors } = useFormErrors();

const data = reactive({
  credentials: null,
  department: "",
  designation: "",
  emailCcs: "",
  emails: "",
  firstName: "",
  hasCredentials: false,
  lastName: "",
  mobiles: "",
  nationality: "",
  needsVisaLetter: false,
  organization: "",
  passport: null,
  passportDateOfExpiry: "",
  passportDateOfIssue: "",
  passportNumber: "",
  phones: "",
  title: "",
});

if (invitation.participant) {
  Object.assign(data, {
    ...invitation.participant,
    emailCcs: invitation.participant.emailCcs?.[0] ?? "",
    emails: invitation.participant.emails?.[0] ?? "",
    mobiles: invitation.participant.mobiles?.[0] ?? "",
    organization: invitation.participant.organization?.id ?? "",
    phones: invitation.participant.phones?.[0] ?? "",
  });
}

function fileToBase64(file: File | null) {
  return new Promise((resolve, reject) => {
    if (!file) {
      resolve(null);
      return;
    }

    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      const base64String = reader.result as string;
      const base64Data = base64String.split(",")[1];
      resolve({
        data: base64Data,
        filename: file.name,
      });
    };
    reader.onerror = () => reject(new Error(`Error while reading file.`));
  });
}

async function saveForm() {
  loading.value = true;
  const url = invitation.participantId
    ? `/events-nominations/${invitation.token}/update-contact/${invitation.participantId}/`
    : `/events-nominations/${invitation.token}/create-contact/`;

  try {
    const newContact = (
      await api.post<Contact>(url, {
        ...data,
        credentials: data.hasCredentials ? await fileToBase64(data.credentials) : null,
        emailCcs: toList(data.emailCcs),
        emails: toList(data.emails),
        mobiles: toList(data.mobiles),
        passport: data.needsVisaLetter ? await fileToBase64(data.passport) : null,
        phones: toList(data.phones),
      })
    ).data;
    await invitation.loadContacts();
    await router.push({ name: "nominate-participant", params: { participantId: newContact.id } });
  } catch (e) {
    setErrors(e);
  } finally {
    loading.value = false;
  }
}

function toList(val: string) {
  if (!val) return [];
  return [val];
}
</script>

<style scoped lang="scss">
.small-input {
  max-width: 5rem;
}
</style>
