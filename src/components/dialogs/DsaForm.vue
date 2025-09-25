<template>
  <q-dialog v-bind="$attrs">
    <q-card style="width: 40rem">
      <q-card-section class="row items-center q-pb-none">
        <div class="text-h6">Edit DSA for {{ registration.contact.fullName }} - {{ registration.event.code }}</div>
        <q-space />
        <q-btn v-close-popup icon="close" flat round dense />
      </q-card-section>

      <q-card-section>
        <q-inner-loading :showing="isLoading">
          <q-spinner-gears size="4rem" color="secondary" />
        </q-inner-loading>

        <q-form class="q-gutter-xs" @submit="onSubmit">
          <q-input
            v-model="data.umojaTravel"
            label="Umoja Travel #"
            :error="!!errors.umojaTravel"
            :error-message="errors.umojaTravel"
            name="umojaTravel"
            outlined
            dense
          />
          <q-input
            v-model="data.bp"
            label="BP #"
            :error="!!errors.bp"
            :error-message="errors.bp"
            name="bp"
            outlined
            dense
          />
          <q-input
            v-model="data.arrivalDate"
            :error="!!errors.arrivalDate"
            :error-message="errors.arrivalDate"
            name="arrivalDate"
            outlined
            dense
            mask="####-##-##"
            label="Arrival Date"
            class="col"
          >
            <template #append>
              <q-icon name="event" class="cursor-pointer">
                <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                  <q-date v-model="data.arrivalDate" mask="YYYY-MM-DD">
                    <div class="row items-center justify-end">
                      <q-btn v-close-popup label="Close" color="primary" flat />
                    </div>
                  </q-date>
                </q-popup-proxy>
              </q-icon>
            </template>
          </q-input>
          <q-input
            v-model="data.departureDate"
            :error="!!errors.departureDate"
            :error-message="errors.departureDate"
            name="departureDate"
            outlined
            dense
            mask="####-##-##"
            label="Departure Date"
            class="col"
          >
            <template #append>
              <q-icon name="event" class="cursor-pointer">
                <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                  <q-date v-model="data.departureDate" mask="YYYY-MM-DD">
                    <div class="row items-center justify-end">
                      <q-btn v-close-popup label="Close" color="primary" flat />
                    </div>
                  </q-date>
                </q-popup-proxy>
              </q-icon>
            </template>
          </q-input>
          <q-input
            v-model="data.cashCard"
            label="Cash Card"
            :error="!!errors.cashCard"
            :error-message="errors.cashCard"
            name="cashCard"
            outlined
            dense
          />
          <encrypted-file-input
            v-model="data.passport"
            :error="!!errors.passport"
            :error-message="errors.passport"
            name="passport"
            clearable
            label="Passport"
            outlined
            dense
            :accept="fileAccept"
          />
          <encrypted-file-input
            v-model="data.boardingPass"
            :error="!!errors.boardingPass"
            :error-message="errors.boardingPass"
            name="boardingPass"
            clearable
            label="Boarding Pass"
            outlined
            dense
            :accept="fileAccept"
          />
          <encrypted-file-input
            v-model="data.signature"
            :error="!!errors.signature"
            :error-message="errors.signature"
            name="signature"
            clearable
            label="Signature"
            outlined
            dense
            :accept="fileAccept"
          />
          <q-checkbox
            v-model="data.paidDsa"
            label="Paid DSA"
            :error="!!errors.paidDsa"
            :error-message="errors.paidDSA"
          />
          <div>
            <q-btn label="Submit" type="submit" color="primary" />
          </div>
        </q-form>
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import type { DSA, Registration } from "src/types/registration";

import { api } from "boot/axios";
import EncryptedFileInput from "components/EncryptedFileInput.vue";
import { useQuasar } from "quasar";
import useFormErrors from "src/composables/useFormErrors";
import { reactive, ref } from "vue";

const $q = useQuasar();
const emit = defineEmits<{
  update: [];
}>();
const props = defineProps<{
  registration: Registration;
}>();

const fileAccept = [".jpeg", ".jpg", ".png", "image/jpeg", "image/png"].join(",");
const isLoading = ref(false);
const data = reactive<DSA>({
  arrivalDate: "",
  boardingPass: null,
  bp: "",
  cashCard: "",
  departureDate: "",
  dsaOnArrival: 0,
  id: 0,
  numberOfDays: 0,
  paidDsa: false,
  passport: null,
  registration: 0,
  signature: null,
  totalDsa: "",
  umojaTravel: "",
});
const { errors, setErrors } = useFormErrors();

reset();

async function onSubmit() {
  try {
    isLoading.value = true;
    if (!data.id) {
      await api.post("/dsa/", data);
    } else {
      await api.put(`/dsa/${data.id}/`, data);
    }
    $q.notify({
      message: "DSA saved successfully.",
      type: "positive",
    });
    emit("update");
  } catch (e) {
    setErrors(e);
  } finally {
    isLoading.value = false;
  }
}

function reset() {
  Object.assign(data, props.registration.dsa);
  data.registration = props.registration.id;
}
</script>

<style scoped lang="scss"></style>
