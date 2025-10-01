import { defineBoot } from "#q-app/wrappers";
import * as Sentry from "@sentry/vue";
import { createSentryPiniaPlugin } from "@sentry/vue";
import { useAppSettingsStore } from "stores/appSettingsStore";
import { useUserStore } from "stores/userStore";

/**
 * Initializes the application store and configure sentry.
 */
export default defineBoot(async ({ app, redirect, router, store, urlPath }) => {
  const $q = app.config.globalProperties.$q;
  const userStore = useUserStore();
  const appSettingsStore = useAppSettingsStore();

  try {
    $q.loading.show();
    await Promise.all([userStore.load(), appSettingsStore.load()]);
    const defaultPage = userStore.availablePages[0]?.items[0]?.to;
    if (urlPath === "/" && defaultPage) {
      redirect(userStore.defaultPage);
    }
  } catch (e) {
    // eslint-disable-next-line no-console
    console.log(e);
    $q.notify({
      message: "Unknown error while loading data, please try again later.",
      type: "negative",
    });
  } finally {
    $q.loading.hide();
  }

  if (appSettingsStore.sentryDsn) {
    Sentry.init({
      app,
      dsn: appSettingsStore.sentryDsn,
      environment: appSettingsStore.environmentName,
      integrations: [Sentry.browserTracingIntegration({ router })],
    });
    store.use(createSentryPiniaPlugin());
  }
});
