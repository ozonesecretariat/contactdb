export function unaccentMatch(valueToFind: string, searchFields: (null | string | string[] | undefined)[]) {
  const searchValue = normalizeString(valueToFind);
  for (const field of searchFields) {
    if (!field) {
      continue;
    }
    const searchField = normalizeString(field);
    if (searchField.includes(searchValue)) {
      return true;
    }
  }
  return false;
}

export function unaccentSearch<Row>(
  valueToFind: string,
  rows: Row[],
  extractFunction: (row: Row) => (null | string | string[] | undefined)[],
): Row[] {
  return rows.filter((row) => unaccentMatch(valueToFind, extractFunction(row)));
}

function normalizeString(str: string | string[]) {
  const val = Array.isArray(str) ? str.join(" ") : str;
  return val
    .normalize("NFKD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase();
}
