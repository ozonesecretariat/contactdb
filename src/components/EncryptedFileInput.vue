<template>
  <div class="fileInput">
    <q-file v-model="fileUpload" v-bind="$attrs" style="width: 25rem" />
    <take-photo label="" @capture="setPicture" />
    <q-btn
      color="secondary"
      icon="download"
      :href="modelValue?.data"
      :download="modelValue?.filename"
      :disable="!modelValue"
    ></q-btn>
  </div>
</template>

<script lang="ts" setup>
import type { EncryptedFile } from "src/types/encryptedFile";

import TakePhoto from "components/dialogs/TakePhoto.vue";
import { base64ToFile, fileToBase64Dict } from "src/utils/file";
import { ref, watch } from "vue";

const props = defineProps<{ modelValue: EncryptedFile | null }>();
const emit = defineEmits<{
  "update:modelValue": [value: EncryptedFile | null];
}>();

const fileUpload = ref<File | null>(null);
setModel(props.modelValue);

watch(fileUpload, async (newFile) => {
  const result = await fileToBase64Dict(newFile);
  emit("update:modelValue", result);
});

function setModel(val: EncryptedFile | null) {
  if (!val) {
    fileUpload.value = null;
  } else {
    fileUpload.value = base64ToFile(val.data, val.filename, "image/jpeg");
  }
}

function setPicture(picture: string) {
  fileUpload.value = base64ToFile(picture, `capture-${new Date().toISOString()}.jpeg`, "image/jpeg");
}
</script>

<style scoped lang="scss">
.fileInput {
  display: flex;
  gap: 0.5rem;
  align-items: start;
  width: 100%;
}
</style>
