import type { Country, Region, Subregion } from "src/types/country";
import type { OrganizationType } from "src/types/organization";

export interface EventCount {
  count: number;
  gender: string;
  government: string;
  organizationType: string;
  region: string;
  status: string;
  subregion: string;
}

export interface Statistics {
  countries: Country[];
  organizationTypes: OrganizationType[];
  regions: Region[];
  registrations: EventCount[];
  subregions: Subregion[];
}
