import type { Country } from "src/types/country";

export interface Organization {
  acronym: string;
  address: string;
  city: string;
  country: Country;
  emails: string[];
  faxes: string[];
  government: Country;
  id: number;
  name: string;
  organizationType: string;
  phones: string[];
  postalCode: string;
  state: string;
  websites: string[];
}
