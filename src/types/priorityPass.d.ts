import type { Country } from "src/types/country";
import type { Contact } from "src/types/nomination";
import type { Organization } from "src/types/organization";
import type { Registration } from "src/types/registration";

export interface PriorityPass {
  code: string;
  contact: Contact;
  country: Country | null;
  createdAt: string;
  organization: null | Organization;
  registrations: Registration[];
}
