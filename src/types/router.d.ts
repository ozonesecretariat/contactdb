import "vue-router";

declare module "vue-router" {
  interface RouteMeta {
    header?: string;
    requireAuthentication?: boolean;
    requireAnonymous?: boolean;
    requireStaff?: boolean;
    requireSuperuser?: boolean;
    requirePermissions?: string[];
  }
}
