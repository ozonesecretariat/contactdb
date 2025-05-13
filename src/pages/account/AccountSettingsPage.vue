<template>
  <p>Change basic account information</p>
  <q-form class="q-gutter-md" @submit="onSubmit">
    <q-input
      v-model="firstName"
      autofocus
      autocomplete="family-name"
      label="First name"
      filled
      :error="!!errors.firstName"
      :error-message="errors.firstName"
    />
    <q-input
      v-model="lastName"
      autocomplete="given-name"
      label="Last name"
      filled
      :error="!!errors.lastName"
      :error-message="errors.lastName"
    />
    <q-input
      :model-value="userStore.email"
      label="Email"
      filled
      readonly
      disable
      hint="Email address cannot be changed."
    />
    <div>
      <q-btn type="submit" color="primary" label="Save" class="full-width" :loading="loading" />
    </div>
  </q-form>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useUserStore } from "stores/userStore";
import useFormErrors from "src/composables/useFormErrors";
import { api } from "boot/axios";
import { useQuasar } from "quasar";

const $q = useQuasar();
const userStore = useUserStore();
const { errors, setErrors } = useFormErrors();

const loading = ref(false);
const firstName = ref(userStore.firstName);
const lastName = ref(userStore.lastName);

async function onSubmit() {
  errors.value = {};
  try {
    loading.value = true;
    await api.patch("/auth/user/", {
      firstName: firstName.value,
      lastName: lastName.value,
    });
    $q.notify({
      type: "positive",
      message: "Account details updated.",
    });
    await userStore.load();
  } catch (e) {
    setErrors(e);
  } finally {
    loading.value = false;
  }
}
</script>
