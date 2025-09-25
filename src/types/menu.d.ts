import type { RouteLocationRaw } from "vue-router";

export interface MenuItem {
  click?: () => Promise<void> | void;
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
