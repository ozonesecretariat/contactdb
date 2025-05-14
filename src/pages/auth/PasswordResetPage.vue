<template>
  <q-form class="q-gutter-md" @submit="onSubmit">
    <p>Forgotten your password? Enter your email address below, and we’ll email instructions for setting a new one.</p>
    <q-input
      v-model="email"
      type="email"
      label="Email"
      filled
      autocomplete="email"
      :error="!!errors.email"
      :error-message="errors.email"
    >
      <template #prepend>
        <q-icon name="email" />
      </template>
    </q-input>
    <div>
      <q-btn type="submit" color="primary" label="Reset Password" class="full-width" :loading="loading" />
    </div>
  </q-form>
</template>

<script setup lang="ts">
import { api } from "boot/axios";
import { useQuasar } from "quasar";
import useFormErrors from "src/composables/useFormErrors";
import { ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const $q = useQuasar();
const loading = ref(false);
const { errors, setErrors } = useFormErrors();

const email = ref("");

async function onSubmit() {
  errors.value = {};
  try {
    loading.value = true;
    await api.post("/auth/password/reset/", {
      email: email.value,
    });
    $q.notify({
      message: "Password reset instructions have been sent to your email!",
      type: "positive",
    });
    await router.push({ name: "login" });
  } catch (e) {
    setErrors(e);
  } finally {
    loading.value = false;
  }
}
</script>
