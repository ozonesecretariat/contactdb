import { defineBoot } from "#q-app/wrappers";
import axios, { type AxiosError, type AxiosInstance } from "axios";

declare module "vue" {
  interface ComponentCustomProperties {
    $api: AxiosInstance;
    $axios: AxiosInstance;
  }
}

const apiBaseEndpoint = "/api";

export let apiHost = window.location.host;
export let apiURL = `${window.location.origin}${apiBaseEndpoint}`;
export let apiBase = `${window.location.origin}`;

if (process.env.NODE_ENV === "development") {
  apiHost = "localhost:8000";
  apiURL = `http://localhost:8000${apiBaseEndpoint}`;
  apiBase = "http://localhost:8000";
}

if (process.env.PUBLIC_API_HOST) {
  apiHost = process.env.PUBLIC_API_HOST;
  apiURL = `${window.location.protocol}//${apiHost}${apiBaseEndpoint}`;
  apiBase = `${window.location.protocol}//${apiHost}`;
}

// Be careful when using SSR for cross-request state pollution
// due to creating a Singleton instance here;
// If any client changes this (global) instance, it might be a
// good idea to move this instance creation inside of the
// "export default () => {}" function below (which runs individually
// for each client)
export const api = axios.create({
  baseURL: apiURL,
  headers: {},
  maxRedirects: 5,
  withCredentials: true,
  withXSRFToken: true,
  xsrfCookieName: "csrftoken",
  xsrfHeaderName: "X-CSRFToken",
});

export default defineBoot(({ app }) => {
  const $q = app.config.globalProperties.$q;

  // Add request interceptor
  api.interceptors.request.use(
    (config) => {
      $q.loadingBar.start();
      return config;
    },
    (error: AxiosError) => {
      $q.loadingBar.stop();
      return Promise.reject(error);
    },
  );

  // Add response interceptor
  api.interceptors.response.use(
    (response) => {
      $q.loadingBar.stop();
      return response;
    },
    (error: AxiosError) => {
      $q.loadingBar.stop();
      return Promise.reject(error);
    },
  );

  // for use inside Vue files (Options API) through this.$axios and this.$api
  app.config.globalProperties.$axios = axios;
  // ^ ^ ^ this will allow you to use this.$axios (for Vue Options API form)
  //       so you won't necessarily have to import axios in each vue file

  app.config.globalProperties.$api = api;
  // ^ ^ ^ this will allow you to use this.$api (for Vue Options API form)
  //       so you can easily perform requests against your app's API
});
