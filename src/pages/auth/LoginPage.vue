<template>
  <q-form v-if="step === 'auth'" class="q-gutter-md" @submit="next">
    <q-input
      v-model="email"
      autofocus
      type="email"
      label="Email"
      filled
      autocomplete="email"
      :error="!!errors.username"
      :error-message="errors.username"
    >
      <template #prepend>
        <q-icon name="email" />
      </template>
    </q-input>

    <q-input
      v-model="password"
      :type="isPwd ? 'password' : 'text'"
      label="Password"
      filled
      autocomplete="current-password"
      :error="!!errors.password"
      :error-message="errors.password"
    >
      <template #prepend>
        <q-icon name="lock" />
      </template>
      <template #append>
        <q-icon :name="isPwd ? 'visibility_off' : 'visibility'" class="cursor-pointer" @click="isPwd = !isPwd" />
      </template>
    </q-input>

    <div>
      <q-btn type="submit" color="primary" label="Login" class="full-width" :loading="loading" />
    </div>

    <div class="text-center">
      <router-link to="password-reset">Forgot password?</router-link>
    </div>
  </q-form>
  <q-form v-else-if="step === 'token'" class="q-gutter-md" @submit="next">
    <p>Please input the 2FA token from your authenticator app.</p>
    <q-input
      v-model="code"
      autofocus
      label="Code"
      mask="######"
      filled
      autocomplete="otp"
      :error="!!errors.otp_token"
      :error-message="errors.otp_token"
    />
    <p>
      Alternatively, if you do not have your authenticator app, you can also use one of your
      <a href="#" @click.prevent="step = 'backup'">backup tokens.</a>
    </p>

    <div>
      <q-btn type="submit" color="primary" label="Login" class="full-width" :loading="loading" />
    </div>
  </q-form>
  <q-form v-else-if="step === 'backup'" class="q-gutter-md" @submit="next">
    <p>
      Use this form for entering backup tokens for logging in. These tokens have been generated for you to print and
      keep safe. Please enter one of these backup tokens to login to your account.
    </p>
    <q-input
      v-model="code"
      autofocus
      label="Backup token"
      filled
      autocomplete="otp"
      :error="!!errors.otp_token"
      :error-message="errors.otp_token"
    />
    <div>
      <q-btn type="submit" color="primary" label="Login" class="full-width" :loading="loading" />
    </div>
  </q-form>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import { useQuasar } from "quasar";
import { api } from "src/boot/axios";
import { useRoute, useRouter } from "vue-router";
import { useUserStore } from "stores/userStore";
import useFormErrors from "src/composables/useFormErrors";

const $q = useQuasar();
const route = useRoute();
const userStore = useUserStore();

const email = ref("");
const password = ref("");
const code = ref("");
const isPwd = ref(true);
const { errors, setErrors } = useFormErrors();

const loading = ref(false);
const step = ref("auth");

function getSafeRedirect(path: string | null | undefined) {
  const url = new URL(path ?? "/", window.location.origin);
  if (url.hostname === window.location.hostname) {
    return url.href;
  }
  // eslint-disable-next-line no-console
  console.error("Unsafe redirect detected:", path);
  return new URL("/", window.location.origin).href;
}

async function next() {
  const data = new FormData();
  data.append("current_step", step.value);
  switch (step.value) {
    case "token":
      data.append("token-otp_token", code.value);
      break;
    case "backup":
      data.append("backup-otp_token", code.value);
      break;
    case "auth":
    default:
      data.append("auth-username", email.value);
      data.append("auth-password", password.value);
      break;
  }

  errors.value = {};
  loading.value = true;
  try {
    const response = await api.post("/auth/login/", data);
    if (!response.data.loggedIn) {
      // eslint-disable-next-line require-atomic-updates
      step.value = "token";
    } else {
      await userStore.fetchUser();
      $q.notify({
        type: "positive",
        message: "Login successful!",
      });
      window.location.href = getSafeRedirect(route.query.next?.toString());
    }
  } catch (e) {
    setErrors(e);
  } finally {
    loading.value = false;
  }
}

watch(code, async (newCode) => {
  if (newCode.length === 6) {
    await next();
  }
});
</script>
