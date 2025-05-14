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
import { api } from "boot/axios";
import { useQuasar } from "quasar";
import useFormErrors from "src/composables/useFormErrors";
import { useUserStore } from "stores/userStore";
import { ref } from "vue";

const $q = useQuasar();
const userStore = useUserStore();

const backupTokens = ref<string[]>([]);
const { setErrors } = useFormErrors();

async function disableAndReload() {
  try {
    await api.post("/account/two_factor/disable/");
    await userStore.load();
  } catch (e) {
    setErrors(e);
  }
}

function disableTwoFactor() {
  $q.dialog({
    cancel: true,
    message:
      "Disabling two factor authentication for your account will significantly reduce your account's security. Are you sure?",
    ok: {
      color: "negative",
      label: "Disable",
    },
    persistent: true,
    title: "Disable 2FA",
  }).onOk(() => {
    disableAndReload();
  });
}

async function generateBackupTokens() {
  try {
    backupTokens.value = (await api.post("/account/two_factor/backup/tokens/")).data.tokens;
  } catch (e) {
    setErrors(e);
  }
}
</script>

<style scoped lang="scss"></style>
