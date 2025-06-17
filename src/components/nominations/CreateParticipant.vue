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
  </q-card-section>
  <q-card-section class="modal-footer">
    <q-btn :to="{ name: 'find-participant' }">Cancel</q-btn>
    <q-btn color="accent" :loading="loading" @click="createParticipant">Save</q-btn>
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
  department: "",
  designation: "",
  emailCcs: "",
  emails: "",
  firstName: "",
  lastName: "",
  mobiles: "",
  organization: "",
  phones: "",
  title: "",
});

async function createParticipant() {
  loading.value = true;
  try {
    const newContact = (
      await api.post<Contact>(`/events-nominations/${invitation.token}/create-contact/`, {
        ...data,
        emailCcs: [data.emailCcs],
        emails: [data.emails],
        mobiles: [data.mobiles],
        phones: [data.phones],
      })
    ).data;
    await invitation.loadContacts();
    await router.push({ name: "verify-participant", params: { participantId: newContact.id } });
  } catch (e) {
    setErrors(e);
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped lang="scss">
.small-input {
  max-width: 5rem;
}
</style>
