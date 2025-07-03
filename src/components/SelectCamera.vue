<template>
  <q-select
    :model-value="modelValue"
    :options="cameras"
    option-value="deviceId"
    option-label="label"
    label="Select Camera"
    dense
    outlined
    @update:model-value="$emit('update:model-value', $event)"
  />
</template>

<script setup lang="ts">
import { useStorage } from "@vueuse/core";
import { useQuasar } from "quasar";
import { onMounted, ref, watch } from "vue";

const props = defineProps<{
  modelValue: MediaDeviceInfo | null;
}>();

const emit = defineEmits<{
  "update:model-value": [value: MediaDeviceInfo | null];
}>();

const $q = useQuasar();
const cameras = ref<MediaDeviceInfo[]>([]);
const storedCameraId = useStorage("selectedCameraId", "");

onMounted(getCameras);

async function getCameras() {
  try {
    const devices = await navigator.mediaDevices.enumerateDevices();
    cameras.value = devices.filter((device) => device.kind === "videoinput");

    if (cameras.value.length > 0) {
      const storedCamera = cameras.value.find((camera) => camera.deviceId === storedCameraId.value);
      if (!props.modelValue) {
        emit("update:model-value", storedCamera ?? cameras.value[0] ?? null);
      }
    }
  } catch (error) {
    $q.notify({
      message: "Could not get camera list.",
      type: "negative",
    });
    throw error;
  }
}

watch(
  () => props.modelValue?.deviceId,
  (newId) => {
    if (newId) {
      storedCameraId.value = newId;
    }
  },
);
</script>

<style scoped lang="scss"></style>
