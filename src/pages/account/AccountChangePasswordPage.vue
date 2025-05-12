<template>
  <p>Change current password</p>
  <q-form class="q-gutter-md" @submit="onSubmit">
    <q-input
      v-model="oldPassword"
      autofocus
      :type="isPwdOld ? 'password' : 'text'"
      label="Current Password"
      filled
      autocomplete="current-password"
      :error="!!errors.oldPassword"
      :error-message="errors.oldPassword"
    >
      <template #prepend>
        <q-icon name="lock" />
      </template>
      <template #append>
        <q-icon
          :name="isPwdOld ? 'visibility_off' : 'visibility'"
          class="cursor-pointer"
          @click="isPwdOld = !isPwdOld"
        />
      </template>
    </q-input>
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
const oldPassword = ref("");
const newPassword1 = ref("");
const newPassword2 = ref("");
const isPwd1 = ref(true);
const isPwd2 = ref(true);
const isPwdOld = ref(true);

async function onSubmit() {
  errors.value = {};
  try {
    loading.value = true;
    await api.post("/auth/password/change/", {
      oldPassword: oldPassword.value,
      newPassword1: newPassword1.value,
      newPassword2: newPassword2.value,
    });
    $q.notify({
      type: "positive",
      message: "Password changed successfully.",
    });
    await userStore.fetchUser();
  } catch (e) {
    setErrors(e);
  } finally {
    loading.value = false;
  }
}
</script>
