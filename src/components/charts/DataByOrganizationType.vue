<template>
  <v-chart
    autoresize
    :theme="$q.dark.isActive ? 'dark' : ''"
    :option="{
      title: { text: 'Participants by organization type' },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow',
        },
      },
      legend: {},
      xAxis: {
        type: 'value',
      },
      yAxis: {
        type: 'category',
        data: typesInOrder,
        inverse: true,
      },
      series,
    }"
  />
</template>

<script setup lang="ts">
import type { EventCount, Statistics } from "src/types/statistics";

import { BarChart } from "echarts/charts";
import { GridComponent, LegendComponent, TitleComponent, TooltipComponent } from "echarts/components";
import { use } from "echarts/core";
import { SVGRenderer } from "echarts/renderers";
import { useQuasar } from "quasar";
import { RegistrationStatusChoices } from "src/constants";
import { computed } from "vue";
import VChart from "vue-echarts";

use([TitleComponent, TooltipComponent, LegendComponent, BarChart, GridComponent, SVGRenderer]);

const $q = useQuasar();

const props = defineProps<{ entries: EventCount[]; statistics: Statistics }>();

const namesMap = computed(() =>
  Object.fromEntries(
    props.statistics.organizationTypes.map((type) => [type.acronym, type.statisticsTile || type.title]),
  ),
);
const typesInOrder = computed(() => {
  const result: string[] = [];
  for (const type of props.statistics.organizationTypes) {
    const name = type.statisticsTile || type.title;
    if (!result.includes(name)) {
      result.push(name);
    }
  }
  return result;
});

const series = computed(() => {
  const result = Object.fromEntries(
    RegistrationStatusChoices.map((status) => {
      const item = {
        data: typesInOrder.value.map(() => 0),
        emphasis: {
          focus: "series",
        },
        name: status,
        stack: "total",
        type: "bar",
      };
      return [status, item];
    }),
  );

  for (const entry of props.entries) {
    const name = namesMap.value[entry.organizationType] ?? "";
    const index = typesInOrder.value.indexOf(name);
    const item = result[entry.status];
    if (item && typeof item.data[index] === "number") {
      item.data[index] += entry.count;
    }
  }

  return Object.values(result);
});
</script>

<style scoped lang="scss"></style>
