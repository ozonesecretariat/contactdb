import type { Statistics } from "src/types/statistics";

export function getChartSeries<T extends object>(
  stats: Statistics,
  key1: keyof Statistics["schema"],
  key2: keyof Statistics["schema"],
  options: T,
) {
  const level1Categories = stats.schema[key1];
  const level2Categories = stats.schema[key2];

  const result = Object.fromEntries(
    level1Categories.map((cat1) => {
      const series = {
        ...options,
        data: level2Categories.map(() => 0),
        name: cat1,
      };
      return [cat1, series];
    }),
  );

  for (const entry of stats.registrations) {
    const cat1 = entry[key1] || "N/A";
    const cat2 = entry[key2] || "N/A";
    const index = level2Categories.indexOf(cat2);
    const item = result[cat1];
    if (item && typeof item.data[index] === "number") {
      item.data[index] += entry.count;
    }
  }

  return Object.values(result);
}
