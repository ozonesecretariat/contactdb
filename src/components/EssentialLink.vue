<template>
  <QItem clickable tag="a" target="_blank" :href="link">
    <QItemSection v-if="icon" avatar>
      <QIcon :name="icon" />
    </QItemSection>

    <QItemSection>
      <QItemLabel>{{ title }}</QItemLabel>
      <QItemLabel caption>{{ caption }}</QItemLabel>
    </QItemSection>
  </QItem>
</template>

<script setup lang="ts">
export interface EssentialLinkProps {
  title: string;
  caption?: string;
  link?: string;
  icon?: string;
}

withDefaults(defineProps<EssentialLinkProps>(), {
  caption: "",
  link: "#",
  icon: "",
});
</script>
