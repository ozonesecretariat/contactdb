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
          {{ participant.organization?.name }}
        </div>
        <div v-if="participant.organization?.government" class="text-h6">
          {{ participant.organization?.government?.name }}
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
        <div>
          Email: {{ participant.emails?.[0] ?? "-" }}
          <br />
          Mobile: {{ participant.mobiles?.[0] ?? "-" }}
        </div>
      </div>
    </div>
    <div class="col-2 q-gutter-y-md">
      <slot name="buttons"></slot>
      <q-img v-if="participant.hasPhoto" :src="photoUrl" alt="" />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Contact } from "src/types/nomination";

import { computed } from "vue";

const props = defineProps<{
  participant: Contact;
  photoUrl: string;
}>();
const country = computed(() => {
  if (props.participant?.isUseOrganizationAddress) {
    return props.participant.organization?.country?.name ?? props.participant.organization?.government?.name;
  }
  return props.participant?.countryName;
});
const addressEntity = computed(() =>
  props.participant?.isUseOrganizationAddress ? props.participant?.organization : props.participant,
);
</script>

<style scoped lang="scss"></style>
