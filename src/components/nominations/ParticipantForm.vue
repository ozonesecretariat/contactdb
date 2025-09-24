<template>
  <q-card-section class="col-grow column">
    <div class="flex q-gutter-md">
      <q-select
        v-model="data.title"
        :options="titles"
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
        class="col-grow"
      />
      <q-input
        v-model="data.lastName"
        :error="!!errors.lastName"
        :error-message="errors.lastName"
        outlined
        label="Last Name"
        name="lastName"
        class="col-grow"
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
      label="Job title"
      name="designation"
    />
    <q-input
      v-model="data.department"
      :error="!!errors.department"
      :error-message="errors.department"
      outlined
      label="Department, Division or Unit (within the organization)"
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
    <q-select
      v-model="data.gender"
      :options="genders"
      :error="!!errors.gender"
      :error-message="errors.gender"
      outlined
      label="Gender"
      name="gender"
    />
    <q-file
      v-model="data.photo"
      :error="!!errors.photo"
      :error-message="errors.photo"
      name="photo"
      outlined
      accept=".jpeg,.jpg,.png"
      :label="data.hasPhoto ? 'Change photo' : 'Add photo'"
    >
      <template #append>
        <q-btn v-if="data.hasPhoto" label="View current" @click="currentImageDialog = true" />
      </template>
    </q-file>
    <q-dialog v-model="currentImageDialog">
      <q-card class="bg-primary text-white" style="width: 800px; max-width: 90vw">
        <q-card-section class="row items-center">
          <div class="text-h6">Current photo</div>
          <q-space />
          <q-btn v-close-popup flat round dense icon="close" />
        </q-card-section>
        <q-card-section v-if="data.id">
          <q-img :src="invitation.getPhotoUrl(data.id)" alt="" style="max-height: 80vh" />
        </q-card-section>
      </q-card>
    </q-dialog>
    <div class="text-subtitle2">Address</div>
    <q-checkbox
      v-model="data.isUseOrganizationAddress"
      label="Use organization address"
      :error="!!errors.isUseOrganizationAddress"
      :error-message="errors.isUseOrganizationAddress"
      name="isUseOrganizationAddress"
    />
    <template v-if="!data.isUseOrganizationAddress">
      <div class="address-row">
        <q-select
          v-model="data.country"
          :options="countries"
          option-value="code"
          option-label="name"
          map-options
          emit-value
          outlined
          label="Country"
          use-input
          input-debounce="0"
          :error="!!errors.country"
          :error-message="errors.country"
          @filter="searchCountries"
        >
          <template #no-option>
            <q-item>
              <q-item-section class="text-grey">No results</q-item-section>
            </q-item>
          </template>
        </q-select>
        <q-input
          v-model="data.city"
          :error="!!errors.city"
          :error-message="errors.city"
          outlined
          label="City"
          name="city"
        />
      </div>
      <div class="address-row">
        <q-input
          v-model="data.state"
          :error="!!errors.state"
          :error-message="errors.state"
          outlined
          label="State"
          name="state"
        />
        <q-input
          v-model="data.postalCode"
          :error="!!errors.postalCode"
          :error-message="errors.postalCode"
          outlined
          label="Postal Code"
          name="postalCode"
        />
      </div>
      <q-input
        v-model="data.address"
        :error="!!errors.address"
        :error-message="errors.address"
        outlined
        type="textarea"
        label="Address"
        name="address"
      />
    </template>
    <template v-else>
      <div class="text-subtitle2">Organization Address</div>
      <p>
        {{ selectedOrganization?.address }}
        <br />
        {{ selectedOrganization?.city }} {{ selectedOrganization?.state }} {{ selectedOrganization?.postalCode }}
        <br />
        {{ selectedOrganization?.country?.name }}
      </p>
    </template>
    <div class="text-subtitle2">Files</div>
    <template v-if="selectedOrganization?.organizationType === 'GOV'">
      <q-checkbox
        v-model="data.hasCredentials"
        :error="!!errors.hasCredentials"
        :error-message="errors.hasCredentials"
        name="hasCredentials"
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
          name="credentials"
        >
          <template #append>
            <q-icon name="attach_file" />
          </template>
        </q-file>
      </div>
    </template>
    <q-checkbox
      v-model="data.needsVisaLetter"
      :error="!!errors.needsVisaLetter"
      :error-message="errors.needsVisaLetter"
      name="needsVisaLetter"
      label="Needs visa letter"
    />
    <div v-if="data.needsVisaLetter">
      <div class="row full-width">
        <q-input
          v-model="data.passportNumber"
          :error="!!errors.passportNumber"
          :error-message="errors.passportNumber"
          name="passportNumber"
          label="Passport number"
          outlined
          class="col"
        />
        <q-input
          v-model="data.nationality"
          :error="!!errors.nationality"
          :error-message="errors.nationality"
          name="nationality"
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
          name="passportDateOfIssue"
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
          name="passportDateOfExpiry"
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
        name="passport"
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
import type { Contact } from "src/types/nomination";
import type { QSelectOnFilterUpdate } from "src/types/quasar";

import { api } from "boot/axios";
import useFormErrors from "src/composables/useFormErrors";
import { fileToBase64, fileToBase64Dict } from "src/utils/file";
import { unaccentSearch } from "src/utils/search";
import { useInvitationStore } from "stores/invitationStore";
import { computed, reactive, ref } from "vue";
import { useRouter } from "vue-router";

const loading = ref(false);
const invitation = useInvitationStore();
const router = useRouter();
const { errors, setErrors } = useFormErrors();

const countries = ref(invitation.countries);

const currentImageDialog = ref(false);
const data = reactive({
  address: "",
  city: "",
  country: "",
  credentials: null,
  department: "",
  designation: "",
  emailCcs: "",
  emails: "",
  firstName: "",
  gender: "",
  hasCredentials: false,
  hasPhoto: false,
  id: null,
  isUseOrganizationAddress: false,
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
  photo: null,
  postalCode: "",
  state: "",
  title: "",
});
const selectedOrganization = computed(() =>
  invitation.organizations.find((o) => o.id.toString() === data.organization.toString()),
);
const titles = ["", "Mr.", "Ms.", "H.E. Mr.", "H.E. Ms.", "Hon. Mr.", "Hon. Ms."];
const genders = ["Male", "Female", "Other", "Choose not to disclose"];

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

// Auto-select the org if there is only one
if (invitation.organizations.length === 1 && invitation.organizations?.[0]?.id) {
  Object.assign(data, { organization: data.organization || invitation.organizations?.[0]?.id });
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
        address: data.address,
        city: data.city,
        credentials: data.hasCredentials ? await fileToBase64Dict(data.credentials) : null,
        emailCcs: toList(data.emailCcs),
        emails: toList(data.emails),
        mobiles: toList(data.mobiles),
        passport: data.needsVisaLetter ? await fileToBase64Dict(data.passport) : null,
        phones: toList(data.phones),
        photo: await fileToBase64(data.photo),
        postalCode: data.postalCode,
        state: data.state,
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

function searchCountries(valueToFind: string, update: QSelectOnFilterUpdate) {
  update(() => {
    countries.value = unaccentSearch(valueToFind, invitation.countries, (row) => [
      row.code,
      row.name,
      row.officialName,
    ]);
  });
}

function toList(val: string) {
  if (!val) return [];
  return [val];
}
</script>

<style scoped lang="scss">
.small-input {
  min-width: 7rem;
}

.address-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}
</style>
