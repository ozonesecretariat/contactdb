<template>
  <q-dialog v-model="showDialog">
    <q-card>
      <q-card-section class="row items-center q-pb-none">
        <div class="text-h6">Scan QR code</div>
        <q-space />
        <q-btn v-close-popup icon="close" flat round dense />
      </q-card-section>

      <q-card-section>
        <q-inner-loading :showing="isLoading">
          <q-spinner-gears size="4rem" color="secondary" />
        </q-inner-loading>
        <qrcode-stream :track="paintBoundingBox" @detect="onDetect" @error="onError" @camera-on="isLoading = false" />
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { apiHost } from "boot/axios";
import { useQuasar } from "quasar";
import { ref } from "vue";
import { type DetectedBarcode, type EmittedError, QrcodeStream } from "vue-qrcode-reader";

const $q = useQuasar();
const isLoading = ref(true);
const showDialog = ref(false);
const emit = defineEmits({ code: (code: string) => code || code === "" });

function isValidHost(url: URL) {
  const host = url.host.toLowerCase();
  return host === apiHost.toLowerCase() || host === window.location.host.toLowerCase();
}

function onDetect(detectedCodes: DetectedBarcode[]) {
  for (const detectedCode of detectedCodes) {
    const url = new URL(detectedCode.rawValue);
    const code = url.searchParams.get("code");
    if (isValidHost(url) && code) {
      showDialog.value = false;
      emit("code", code);
      return;
    }
  }

  $q.notify({
    message: "QR code is not valid.",
    type: "negative",
  });
}

function onError(error: EmittedError) {
  $q.notify({
    message: `Could not scan QR code: ${error.name}.`,
    type: "negative",
  });
}

function paintBoundingBox(detectedCodes: DetectedBarcode[], ctx: CanvasRenderingContext2D) {
  for (const detectedCode of detectedCodes) {
    const {
      boundingBox: { height, width, x, y },
    } = detectedCode;

    ctx.lineWidth = 4;
    ctx.strokeStyle = "#007fc2";
    ctx.strokeRect(x, y, width, height);
  }
}

function show() {
  isLoading.value = true;
  showDialog.value = true;
}

defineExpose({ show });
</script>

<style scoped lang="scss"></style>
