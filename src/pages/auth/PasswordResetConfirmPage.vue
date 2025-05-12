<template>
  <q-form class="q-gutter-md" @submit="onSubmit">
    <p>Please enter your new password twice.</p>
    <q-input
      v-model="newPassword1"
      :type="isPwd1 ? 'password' : 'text'"
      label="New Password"
      filled
      autocomplete="new-password"
      :error="!!errors.newPassword1"
      :error-message="errors.newPassword1"
    >
      <template #prepend>
        <q-icon name="lock" />
      </template>
      <template #append>
        <q-icon :name="isPwd1 ? 'visibility_off' : 'visibility'" class="cursor-pointer" @click="isPwd1 = !isPwd1" />
      </template>
    </q-input>

    <q-input
      v-model="newPassword2"
      :type="isPwd2 ? 'password' : 'text'"
      label="Confirm New Password"
      filled
      autocomplete="new-password"
      :error="!!errors.newPassword2"
      :error-message="errors.newPassword2"
    >
      <template #prepend>
        <q-icon name="lock" />
      </template>
      <template #append>
        <q-icon :name="isPwd2 ? 'visibility_off' : 'visibility'" class="cursor-pointer" @click="isPwd2 = !isPwd2" />
      </template>
    </q-input>

    <div>
      <q-btn type="submit" color="primary" label="Change Password" class="full-width" :loading="loading" />
    </div>
  </q-form>
</template>

<script setup lang="ts">
import { useQuasar } from "quasar";
import { ref } from "vue";
import useFormErrors from "src/composables/useFormErrors";
import { api } from "boot/axios";
import { useRouter, useRoute } from "vue-router";

const router = useRouter();
const route = useRoute();
const $q = useQuasar();
const loading = ref(false);
const { errors, setErrors } = useFormErrors();

const newPassword1 = ref("");
const newPassword2 = ref("");
const isPwd1 = ref(true);
const isPwd2 = ref(true);

async function onSubmit() {
  errors.value = {};
  try {
    loading.value = true;
    await api.post("/auth/password/reset/confirm/", {
      newPassword1: newPassword1.value,
      newPassword2: newPassword2.value,
      uid: route.query.uid,
      token: route.query.token,
    });
    $q.notify({
      type: "positive",
      message: "Password has been reset successfully!",
    });
    await router.push({ name: "login" });
  } catch (e) {
    setErrors(e);
  } finally {
    loading.value = false;
  }
}
</script>
