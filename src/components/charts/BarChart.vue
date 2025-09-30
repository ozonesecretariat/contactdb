<template>
  <q-card>
    <v-chart autoresize :theme="$q.dark.isActive ? 'dark' : ''" :option="options" />
  </q-card>
</template>

<script setup lang="ts">
import type { Statistics } from "src/types/statistics";

import { BarChart } from "echarts/charts";
import { GridComponent, LegendComponent, TitleComponent, TooltipComponent } from "echarts/components";
import { use } from "echarts/core";
import { SVGRenderer } from "echarts/renderers";
import { useQuasar } from "quasar";
import { ChartColors } from "src/constants";
import { getChartSeries } from "src/utils/chart";
import { computed } from "vue";
import VChart from "vue-echarts";

use([TitleComponent, TooltipComponent, LegendComponent, BarChart, GridComponent, SVGRenderer]);

const $q = useQuasar();

const props = defineProps<{
  horizontal: boolean;
  key1: keyof Statistics["schema"];
  key2: keyof Statistics["schema"];
  stack: boolean;
  stats: Statistics;
  title: string;
}>();

const options = computed(() => {
  const valueAxis = { type: "value" };
  const categoryAxis = { data: props.stats.schema[props.key2], inverse: props.horizontal, type: "category" };
  const series = getChartSeries(props.stats, props.key1, props.key2, {
    emphasis: {
      focus: "series",
    },
    stack: props.stack ? "total" : null,
    type: "bar",
  });

  return {
    color: ChartColors,
    legend: {},
    series,
    title: { text: props.title },
    tooltip: {
      axisPointer: {
        type: "shadow",
      },
      trigger: "axis",
    },
    xAxis: props.horizontal ? valueAxis : categoryAxis,
    yAxis: !props.horizontal ? valueAxis : categoryAxis,
  };
});
</script>
