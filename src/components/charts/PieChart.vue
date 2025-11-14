<template>
  <q-card :aria-label="title">
    <v-chart autoresize :theme="$q.dark.isActive ? 'dark' : ''" :option="options" />
  </q-card>
</template>

<script setup lang="ts">
import type { Statistics } from "src/types/statistics";

import { PieChart } from "echarts/charts";
import { AriaComponent, LegendComponent, TitleComponent, TooltipComponent } from "echarts/components";
import { use } from "echarts/core";
import { SVGRenderer } from "echarts/renderers";
import { useQuasar } from "quasar";
import { ChartColors } from "src/constants";
import { computed } from "vue";
import VChart from "vue-echarts";

use([AriaComponent, TitleComponent, TooltipComponent, LegendComponent, PieChart, SVGRenderer]);

const $q = useQuasar();
const props = defineProps<{
  key1: keyof Statistics["schema"];
  stats: Statistics;
  title: string;
}>();

const data = computed(() => {
  const counts = Object.fromEntries(
    (props.stats.schema[props.key1] ?? []).map((name) => [
      name,
      {
        name,
        value: 0,
      },
    ]),
  );
  for (const entry of props.stats.registrations) {
    const item = counts[entry[props.key1]];
    if (item) {
      item.value += entry.count;
    }
  }
  return Array.from(Object.values(counts));
});

const options = computed(() => ({
  aria: { show: true },
  color: ChartColors,
  legend: { orient: "horizontal" },
  series: [
    {
      data: data.value,
      name: props.title,
      type: "pie",
    },
  ],
  title: { text: props.title },
  tooltip: {
    trigger: "item",
  },
}));
</script>

<style scoped></style>
