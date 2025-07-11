/* eslint-disable @typescript-eslint/no-explicit-any */

import type { QSelect, QTableColumn } from "quasar";

export type QSelectOnFilterUpdate = (callbackFn: () => void, afterFn?: (ref: QSelect) => void) => void;

export interface QTableColumnWithTooltip<
  Row extends Record<string, any> = any,
  Key = keyof Row extends string ? keyof Row : string,
  Field = ((row: Row) => any) | Key,
> extends QTableColumn<Row, Key, Field> {
  tooltip?: string;
}
