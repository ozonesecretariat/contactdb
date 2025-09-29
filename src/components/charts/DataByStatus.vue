<template>
  <v-chart
    autoresize
    :theme="$q.dark.isActive ? 'dark' : ''"
    :option="{
      title: { text: 'Registration status' },
      tooltip: {
        trigger: 'item',
      },
      legend: { orient: 'horizontal' },
      series: [
        {
          name: 'Participants',
          type: 'pie',
          data: data,
        },
      ],
    }"
  />
</template>

<script setup lang="ts">
import type { EventCount, Statistics } from "src/types/statistics";

import { PieChart } from "echarts/charts";
import { LegendComponent, TitleComponent, TooltipComponent } from "echarts/components";
import { use } from "echarts/core";
import { SVGRenderer } from "echarts/renderers";
import { useQuasar } from "quasar";
import { RegistrationStatusChoices } from "src/constants";
import { computed } from "vue";
import VChart from "vue-echarts";

use([TitleComponent, TooltipComponent, LegendComponent, PieChart, SVGRenderer]);

const $q = useQuasar();

const props = defineProps<{ entries: EventCount[]; statistics: Statistics }>();
const data = computed(() => {
  const counts = Object.fromEntries(
    RegistrationStatusChoices.map((status) => [
      status,
      {
        name: status,
        value: 0,
      },
    ]),
  );
  for (const entry of props.entries) {
    const item = counts[entry.status];
    if (item) {
      item.value += entry.count;
    }
  }
  return Array.from(Object.values(counts));
});
</script>

<style scoped lang="scss"></style>
