<template>
  <QLayout view="lHh Lpr lFf">
    <QHeader elevated>
      <QToolbar>
        <QBtn flat dense round icon="menu" aria-label="Menu" @click="toggleLeftDrawer" />

        <QToolbarTitle>Quasar App</QToolbarTitle>

        <div>Quasar v{{ $q.version }}</div>
      </QToolbar>
    </QHeader>

    <QDrawer v-model="leftDrawerOpen" show-if-above bordered>
      <QList>
        <QItemLabel header>Essential Links</QItemLabel>

        <EssentialLink v-for="link in linksList" :key="link.title" v-bind="link" />
      </QList>
    </QDrawer>

    <QPageContainer>
      <RouterView />
    </QPageContainer>
  </QLayout>
</template>

<script setup lang="ts">
import { ref } from "vue";
import EssentialLink, { type EssentialLinkProps } from "components/EssentialLink.vue";

const linksList: EssentialLinkProps[] = [
  {
    title: "Docs",
    caption: "quasar.dev",
    icon: "school",
    link: "https://quasar.dev",
  },
  {
    title: "Github",
    caption: "github.com/quasarframework",
    icon: "code",
    link: "https://github.com/quasarframework",
  },
  {
    title: "Discord Chat Channel",
    caption: "chat.quasar.dev",
    icon: "chat",
    link: "https://chat.quasar.dev",
  },
  {
    title: "Forum",
    caption: "forum.quasar.dev",
    icon: "record_voice_over",
    link: "https://forum.quasar.dev",
  },
  {
    title: "Twitter",
    caption: "@quasarframework",
    icon: "rss_feed",
    link: "https://twitter.quasar.dev",
  },
  {
    title: "Facebook",
    caption: "@QuasarFramework",
    icon: "public",
    link: "https://facebook.quasar.dev",
  },
  {
    title: "Quasar Awesome",
    caption: "Community Quasar projects",
    icon: "favorite",
    link: "https://awesome.quasar.dev",
  },
];

const leftDrawerOpen = ref(false);

function toggleLeftDrawer() {
  leftDrawerOpen.value = !leftDrawerOpen.value;
}
</script>
