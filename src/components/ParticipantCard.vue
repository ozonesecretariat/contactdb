<template>
  <div class="row items-start justify-between q-pa-md">
    <div class="col">
      <div class="col-10 q-gutter-x-lg">
        <p class="text-h6 text-primary">
          {{ participant?.fullName }}
        </p>
        <div class="text-subtitle1">
          {{ participant.designation }}
          <br v-if="participant.designation && participant.department" />
          {{ participant.department }}
        </div>
        <div class="text-h6">
          {{ organization?.name }}
        </div>
        <div v-if="organization?.government" class="text-h6">
          {{ organization?.government?.name }}
        </div>
      </div>
      <div class="row items-start justify-left q-mt-md q-col-gutter-sm">
        <div v-if="addressEntity" class="col-6">
          {{ addressEntity.address }}
          <br v-if="addressEntity.address" />
          {{ addressEntity.city }}
          {{ addressEntity.state }}
          {{ addressEntity.postalCode }}
          <br v-if="addressEntity.city || addressEntity.state || addressEntity.postalCode" />
          {{ country }}
        </div>
        <div v-if="!hideContactInfo">
          Email: {{ participant.emails?.[0] ?? "-" }}
          <br />
          Mobile: {{ participant.mobiles?.[0] ?? "-" }}
        </div>
      </div>
    </div>
    <div class="col-3 q-gutter-y-md">
      <slot name="buttons"></slot>
      <q-img v-if="participant.hasPhoto" :src="photoUrl" alt="contact photo" />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Contact } from "src/types/nomination";
import type { Organization } from "src/types/organization";

import { computed } from "vue";

const props = defineProps<{
  hideContactInfo?: boolean;
  organization?: null | Organization;
  participant: Contact;
  photoUrl: string;
}>();

const organization = computed(() => props.organization ?? props.participant?.organization);
const country = computed(() => {
  if (props.participant?.isUseOrganizationAddress) {
    return organization.value?.country?.name ?? organization.value?.government?.name;
  }
  return props.participant?.countryName;
});
const addressEntity = computed(() =>
  props.participant?.isUseOrganizationAddress ? organization.value : props.participant,
);
</script>

<style scoped lang="scss"></style>
