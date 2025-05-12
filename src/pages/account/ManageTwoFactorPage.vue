<template>
  <h5 class="q-my-none">Generate Backup Tokens (2FA)</h5>
  <p>
    Backup tokens can be used when your primary device is not available. Each token can only be used once. Generating
    tokens will remove any previously generated ones.
  </p>
  <div v-if="backupTokens.length > 0">
    <p>Print these tokens and keep them somewhere safe.</p>
    <ul class="q-ml-4">
      <li v-for="token in backupTokens" :key="token">
        {{ token }}
      </li>
    </ul>
  </div>
  <q-btn label="Generate tokens" @click="generateBackupTokens" />

  <hr class="q-my-lg" />

  <h5 class="q-my-none">Disable Two-Factor Authentication (2FA)</h5>
  <p>While not recommended, you can also disable two-factor authentication for your account.</p>
  <q-btn color="negative" label="Disable 2FA" @click="disableTwoFactor" />
</template>

<script setup lang="ts">
import { ref } from "vue";
import { api } from "boot/axios";
import useFormErrors from "src/composables/useFormErrors";
import { useQuasar } from "quasar";
import { useUserStore } from "stores/userStore";

const $q = useQuasar();
const userStore = useUserStore();

const backupTokens = ref<string[]>([]);
const { setErrors } = useFormErrors();

async function generateBackupTokens() {
  try {
    backupTokens.value = (await api.post("/account/two_factor/backup/tokens/")).data.tokens;
  } catch (e) {
    setErrors(e);
  }
}

async function disableAndReload() {
  try {
    await api.post("/account/two_factor/disable/");
    await userStore.fetchUser();
  } catch (e) {
    setErrors(e);
  }
}

function disableTwoFactor() {
  $q.dialog({
    title: "Disable 2FA",
    message:
      "Disabling two factor authentication for your account will significantly reduce your account's security. Are you sure?",
    cancel: true,
    persistent: true,
    ok: {
      label: "Disable",
      color: "negative",
    },
  }).onOk(() => {
    disableAndReload();
  });
}
</script>

<style scoped lang="scss"></style>
