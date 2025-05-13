<template>
  <q-list>
    <template v-for="item in items.filter((i) => i.show ?? true)" :key="item.label">
      <q-separator v-if="item.type === 'separator'" />
      <q-item v-else v-close-popup clickable :to="item.to" :href="item.href" @click="item.click">
        <q-item-section v-if="item.icon" avatar>
          <q-icon :name="item.icon" />
        </q-item-section>
        <q-item-section>{{ item.label }}</q-item-section>
      </q-item>
    </template>
  </q-list>
</template>

<script setup lang="ts">
import { defineProps } from "vue";
import type { RouteLocationRaw } from "vue-router";

export interface MenuItem {
  label: string;
  icon?: string;
  to?: RouteLocationRaw;
  href?: string;
  click?: () => void;
  type?: "separator" | "item";
  show?: boolean;
}

export interface MenuListProps {
  items: MenuItem[];
}

const { items } = defineProps<MenuListProps>();
</script>

<style scoped lang="scss"></style>
