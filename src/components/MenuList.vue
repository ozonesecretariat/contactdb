<template>
  <q-list>
    <template v-for="item in filteredItems" :key="item.label">
      <q-separator v-if="item.type === 'separator'" />
      <q-item v-else v-close-popup clickable :to="item.to" :href="item.href" exact @click="item.click">
        <q-item-section v-if="item.icon" avatar>
          <q-icon :name="item.icon" />
        </q-item-section>
        <q-item-section>{{ item.label }}</q-item-section>
      </q-item>
    </template>
  </q-list>
</template>

<script setup lang="ts">
import { useRouter, type RouteLocationRaw } from "vue-router";
import { computed } from "vue";
import { hasRoutePermission } from "src/router";

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

const router = useRouter();
const { items } = defineProps<MenuListProps>();

const filteredItems = computed(() =>
  items.filter((item) => {
    if (item.to) {
      const resolvedRoute = router.resolve(item.to);
      if (!hasRoutePermission(resolvedRoute.matched)) {
        return false;
      }
    }
    return item.show ?? true;
  }),
);
</script>

<style scoped lang="scss"></style>
