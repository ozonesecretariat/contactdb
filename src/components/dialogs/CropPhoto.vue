<template>
  <q-btn color="primary" icon="crop" @click="show()">Crop photo</q-btn>
  <q-dialog v-model="showDialog">
    <q-card>
      <q-card-section class="row items-center q-pb-none">
        <div class="text-h6">Crop Picture</div>
        <q-space />
        <q-btn v-close-popup icon="close" flat round dense />
      </q-card-section>

      <q-card-section>
        <q-inner-loading :showing="isLoading">
          <q-spinner-gears size="4rem" color="secondary" />
        </q-inner-loading>

        <div class="crop-container">
          <cropper
            v-if="photoUrl"
            ref="cropperComponent"
            class="cropper"
            :src="photoUrl"
            :stencil-props="{
              aspectRatio: 1,
            }"
            @ready="isLoading = false"
          />
        </div>
        <div class="row justify-center q-mt-md">
          <q-btn color="primary" icon="crop" label="Crop" :disable="isLoading" @click="cropPicture" />
        </div>
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import "vue-advanced-cropper/dist/style.css";
import { useQuasar } from "quasar";
import { ref, useTemplateRef } from "vue";
import { Cropper } from "vue-advanced-cropper";

const $q = useQuasar();

const isLoading = ref(true);
defineProps<{
  photoUrl: string;
}>();

const emit = defineEmits<{
  crop: [imageData: string];
}>();

const showDialog = ref(false);
const cropperComponent = useTemplateRef("cropperComponent");

function cropPicture() {
  if (!cropperComponent.value) return;

  const { canvas } = cropperComponent.value.getResult();
  const dataUrl = canvas?.toDataURL("image/jpeg");
  if (dataUrl) {
    emit("crop", dataUrl);
    showDialog.value = false;
  } else {
    $q.notify({
      message: "Could not crop picture.",
      type: "negative",
    });
  }
}

function show() {
  showDialog.value = true;
}

defineExpose({ show });
</script>

<style scoped lang="scss">
.crop-container {
  width: 100%;
  max-width: 640px;
  min-height: 240px;
  min-width: 480px;
}
</style>
