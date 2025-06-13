/* eslint-disable @typescript-eslint/no-explicit-any */

import type { QTableColumn } from "quasar";

interface QTableColumnWithTooltip<
  Row extends Record<string, any> = any,
  Key = keyof Row extends string ? keyof Row : string,
  Field = ((row: Row) => any) | Key,
> extends QTableColumn<Row, Key, Field> {
  tooltip?: string;
}
