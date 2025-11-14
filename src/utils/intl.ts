type DateInput = null | string | undefined;

const dateFormat = new Intl.DateTimeFormat([], {
  dateStyle: "medium",
});
const dateTimeFormat = new Intl.DateTimeFormat([], {
  dateStyle: "medium",
  timeStyle: "short",
});

export function formatDate(dateString: DateInput) {
  const date = parseDate(dateString);
  if (!date) {
    return "";
  }

  return dateFormat.format(date);
}

export function formatDateTime(dateString: DateInput) {
  const date = parseDate(dateString);
  if (!date) {
    return "";
  }

  return dateTimeFormat.format(date);
}

export function parseDate(date: DateInput) {
  if (!date) return null;

  const stamp = Date.parse(date);
  if (isNaN(stamp)) {
    return null;
  }
  return new Date(stamp);
}
