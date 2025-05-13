import "vue-router";

declare module "vue-router" {
  interface RouteMeta {
    header?: string;
    requireAuthentication?: boolean;
    requireAnonymous?: boolean;
    requiredPermissions?: string[];
  }
}
