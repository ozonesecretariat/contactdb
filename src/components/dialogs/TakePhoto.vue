<template>
  <q-btn color="primary" icon="photo_camera" aria-label="Take photo" @click="show()">{{ label }}</q-btn>
  <q-dialog v-model="showDialog">
    <q-card>
      <q-card-section class="row items-center q-pb-none">
        <div class="text-h6">Take Picture</div>
        <q-space />
        <q-btn v-close-popup icon="close" flat round dense />
      </q-card-section>

      <q-card-section>
        <q-inner-loading :showing="isLoading">
          <q-spinner-gears size="4rem" color="secondary" />
        </q-inner-loading>

        <div class="camera-controls q-mb-md">
          <select-camera v-model="selectedCamera" />
        </div>

        <div class="camera-container">
          <video ref="videoElement" autoplay playsinline />
          <canvas ref="canvasElement" style="display: none" />
        </div>

        <div class="row justify-center q-mt-md">
          <q-btn color="primary" icon="photo_camera" label="Capture" :disable="isLoading" @click="capturePicture" />
        </div>
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import SelectCamera from "components/SelectCamera.vue";
import { useQuasar } from "quasar";
import { onUnmounted, ref, watch } from "vue";

const $q = useQuasar();
const isLoading = ref(true);
const showDialog = ref(false);
const videoElement = ref<HTMLVideoElement | null>(null);
const canvasElement = ref<HTMLCanvasElement | null>(null);
const stream = ref<MediaStream | null>(null);
const selectedCamera = ref<MediaDeviceInfo | null>(null);

const emit = defineEmits<{
  capture: [imageData: string];
}>();
defineProps({
  label: {
    default: "Take photo",
    type: String,
  },
});

function capturePicture() {
  if (!videoElement.value || !canvasElement.value) return;

  const video = videoElement.value;
  const canvas = canvasElement.value;

  // Set canvas dimensions to match video
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;

  const context = canvas.getContext("2d");
  if (!context) return;

  context.drawImage(video, 0, 0, canvas.width, canvas.height);

  // Convert to base64
  const imageData = canvas.toDataURL("image/jpeg");
  emit("capture", imageData);
  showDialog.value = false;
}

async function initCamera() {
  if (!selectedCamera.value) return;

  isLoading.value = true;

  try {
    const constraints = {
      audio: false,
      video: selectedCamera.value ?? { facingMode: "environment" },
    };

    stopCamera();
    stream.value = await navigator.mediaDevices.getUserMedia(constraints);

    if (videoElement.value && stream.value) {
      videoElement.value.srcObject = stream.value;
      isLoading.value = false;
    }
  } catch (error) {
    $q.notify({
      message: "Could not access camera.",
      type: "negative",
    });
    throw error;
  }
}

function show() {
  showDialog.value = true;
}

function stopCamera() {
  if (stream.value) {
    stream.value.getTracks().forEach((track) => track.stop());
    stream.value = null;
  }
}

watch(selectedCamera, initCamera);

watch(showDialog, () => {
  if (showDialog.value) {
    initCamera();
  } else {
    stopCamera();
  }
});

onUnmounted(() => {
  stopCamera();
});
</script>

<style scoped lang="scss">
.camera-container {
  width: 100%;
  max-width: 640px;
  margin: 0 auto;

  video {
    width: 100%;
    height: auto;
  }
}
</style>
