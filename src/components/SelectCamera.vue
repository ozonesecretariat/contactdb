<template>
  <q-select
    :model-value="modelValue"
    @update:model-value="$emit('update:model-value', $event)"
    :options="cameras"
    option-value="deviceId"
    option-label="label"
    label="Select Camera"
    dense
    outlined
  />
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useQuasar } from "quasar";

const props = defineProps<{
  modelValue: MediaDeviceInfo | null;
}>();

const emit = defineEmits<{
  "update:model-value": [value: MediaDeviceInfo | null];
}>();

const $q = useQuasar();
const cameras = ref<MediaDeviceInfo[]>([]);

onMounted(getCameras);

async function getCameras() {
  try {
    const devices = await navigator.mediaDevices.enumerateDevices();
    cameras.value = devices.filter((device) => device.kind === "videoinput");

    // Select the first camera by default if none is selected
    if (cameras.value.length > 0 && !props.modelValue) {
      emit("update:model-value", cameras.value[0] ?? null);
    }
  } catch (error) {
    $q.notify({
      message: "Could not get camera list.",
      type: "negative",
    });
    throw error;
  }
}
</script>

<style scoped lang="scss"></style>
