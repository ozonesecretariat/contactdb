<template>
  <q-list v-for="section in filteredSections" :key="section.name">
    <template v-for="item in section.items" :key="item.label">
      <q-item v-close-popup clickable :to="item.to" :href="item.href" exact @click="item.click">
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
import { hasRoutePermission } from "src/router";
import { computed } from "vue";
import { type RouteLocationRaw, useRouter } from "vue-router";

export interface MenuItem {
  click?: () => void;
  href?: string;
  icon?: string;
  label: string;
  show?: boolean;
  to?: RouteLocationRaw;
}

export interface MenuSection {
  items: MenuItem[];
  name: string;
}

const { items } = defineProps<{
  items: MenuSection[];
}>();
const router = useRouter();

function filterItems(menuItems: MenuItem[]) {
  return menuItems.filter((item) => {
    if (item.to) {
      const resolvedRoute = router.resolve(item.to);
      if (!hasRoutePermission(resolvedRoute.matched)) {
        return false;
      }
    }
    return item.show ?? true;
  });
}

const filteredSections = computed(() => {
  const result: MenuSection[] = items.map((section) => ({
    items: filterItems(section.items),
    name: section.name,
  }));

  return result.filter((section) => section.items.length > 0);
});
</script>

<style scoped lang="scss"></style>
