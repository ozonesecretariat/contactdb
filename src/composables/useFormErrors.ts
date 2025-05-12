import { ref } from "vue";

import type { AxiosError } from "axios";
import { useQuasar } from "quasar";

export type DRFErrorMessage = string | string[];
export type DRFError = { details: Record<string, DRFErrorMessage> } | Record<string, DRFErrorMessage>;

export default function useFormErrors() {
  const $q = useQuasar();
  const errors = ref<Record<string, string>>({});
  return {
    errors,
    setErrors: (axiosError: unknown) => {
      const result: Record<string, string> = {};
      const data = (axiosError as AxiosError<DRFError>).response?.data;
      const reason = data?.details ? data.details : data;

      if (!reason) {
        result.nonFieldErrors = "Unknown error";
      } else {
        for (const [key, value] of Object.entries(reason)) {
          result[key] = Array.isArray(value) ? value.join(" ") : String(value);
        }
      }

      $q.notify({
        type: "negative",
        message: result.nonFieldErrors ?? result.__all__ ?? "Could not submit form.",
      });

      errors.value = result;
    },
  };
}
