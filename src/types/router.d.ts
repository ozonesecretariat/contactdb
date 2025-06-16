import "vue-router";
import type { MetaOptions } from "quasar/dist/types/meta";

declare module "vue-router" {
  interface RouteMeta {
    header?: string;
    metaHeaders?: MetaOptions;
    requireAnonymous?: boolean;
    requireAuthentication?: boolean;
    requirePermissions?: string[];
    requireStaff?: boolean;
    requireSuperuser?: boolean;
    subtitle?: string;
  }
}
