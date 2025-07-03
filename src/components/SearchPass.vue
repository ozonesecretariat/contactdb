<template>
  <q-dialog v-model="showDialog">
    <q-card style="min-width: 400px; min-height: 400px">
      <q-card-section class="row items-center q-pb-none">
        <div class="text-h6">Search Priority Pass</div>
        <q-space />
        <q-btn v-close-popup icon="close" flat round dense />
      </q-card-section>

      <q-card-section>
        <q-input
          v-model="searchQuery"
          label="Search by event, contact, email or organization"
          filled
          dense
          autofocus
          role="search"
          @keyup.enter="searchPasses"
        >
          <template #append>
            <q-icon v-if="searchQuery" name="close" class="cursor-pointer" @click="searchQuery = ''" />
            <q-btn :loading="isLoading" dense flat icon="search" @click="searchPasses" />
          </template>
        </q-input>

        <q-list v-if="passes.length" class="q-mt-md">
          <q-item v-for="pass in passes" :key="pass.code" v-ripple clickable @click="selectPass(pass.code)">
            <q-item-section>
              <q-item-label>{{ pass.registrations.map((r) => r.event.code).join(", ") }}</q-item-label>
              <q-item-label caption>{{ pass.contact?.fullName }} | {{ pass.organization?.name }}</q-item-label>
            </q-item-section>
          </q-item>
        </q-list>

        <div v-else-if="hasSearched" class="text-center q-pa-md text-grey">No priority passes found</div>
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import type { Paginated } from "src/types/pagination";
import type { PriorityPass } from "src/types/priorityPass";

import { api } from "boot/axios";
import { useQuasar } from "quasar";
import { ref } from "vue";

const $q = useQuasar();
const showDialog = ref(false);
const searchQuery = ref("");
const passes = ref<PriorityPass[]>([]);
const isLoading = ref(false);
const hasSearched = ref(false);

const emit = defineEmits({ code: (code: string) => code || code === "" });

async function searchPasses() {
  if (!searchQuery.value.trim()) return;

  isLoading.value = true;
  passes.value = [];

  try {
    const response = await api.get<Paginated<PriorityPass>>("/priority-passes/", {
      params: { page: 1, pageSize: 10, search: searchQuery.value },
    });
    passes.value = response.data.results;
    hasSearched.value = true;
  } catch (e) {
    $q.notify({
      message: "Failed to search priority passes",
      type: "negative",
    });
    throw e;
  } finally {
    isLoading.value = false;
  }
}

function selectPass(code: string) {
  showDialog.value = false;
  emit("code", code);
}

function show() {
  showDialog.value = true;
  searchQuery.value = "";
  passes.value = [];
  hasSearched.value = false;
}

defineExpose({ show });
</script>

<style scoped lang="scss"></style>
