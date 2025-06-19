import type { AxiosError } from "axios";

import { useQuasar } from "quasar";
import { ref } from "vue";

export type DRFErrorMessage = string | string[];
export type DRFErrorResponse = Record<string, DRFErrorMessage> | { details: Record<string, DRFErrorMessage> };

export default function useFormErrors() {
  const $q = useQuasar();
  const errors = ref<Record<string, string>>({});
  return {
    errors,
    setErrors: (axiosError: unknown) => {
      const result: Record<string, string> = {};
      const data = (axiosError as AxiosError<DRFErrorResponse>).response?.data;
      const reason = data?.details ? data.details : data;

      if (!reason) {
        result.nonFieldErrors = "Unknown error";
      } else {
        for (const [key, value] of Object.entries(reason)) {
          let errorMsg = value;
          if (typeof value === "object" && !Array.isArray(value)) {
            errorMsg = Array.from(Object.values(value)).flat();
          }
          result[key] = Array.isArray(errorMsg) ? errorMsg.join(" ") : String(errorMsg);
        }
      }

      $q.notify({
        message: result.nonFieldErrors ?? result.__all__ ?? "Could not submit form.",
        type: "negative",
      });

      errors.value = result;
    },
  };
}
