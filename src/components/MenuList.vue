<template>
  <q-list v-for="section in items" :key="section.name">
    <q-item-label v-if="section.label" header>{{ section.label }}</q-item-label>
    <template v-for="item in section.items" :key="item.label">
      <q-item v-close-popup clickable :to="item.to" :href="item.href" @click="item.click">
        <q-item-section v-if="item.icon" avatar>
          <q-icon :name="item.icon" />
        </q-item-section>
        <q-item-section>{{ item.label }}</q-item-section>
      </q-item>
    </template>
    <q-separator />
  </q-list>
</template>

<script setup lang="ts">
import type { MenuSection } from "src/types/menu";

defineProps<{
  items: MenuSection[];
}>();
</script>

<style scoped lang="scss"></style>
