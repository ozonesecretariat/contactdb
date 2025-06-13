import "vue-router";

declare module "vue-router" {
  interface RouteMeta {
    header?: string;
    requireAnonymous?: boolean;
    requireAuthentication?: boolean;
    requirePermissions?: string[];
    requireStaff?: boolean;
    requireSuperuser?: boolean;
    subtitle?: string;
  }
}
