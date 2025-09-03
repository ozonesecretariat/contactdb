import type { MeetingEvent } from "./event";
import type { Organization } from "./organization";

export interface Contact {
  address: string;
  city: string;
  country: string;
  countryName: string;
  department: string;
  designation: string;
  emailCcs: string[];
  emails: string[];
  firstName: string;
  fullName: string;
  gender: string;
  hasCredentials: boolean;
  hasPhoto: boolean;
  id: number;
  isUseOrganizationAddress: boolean;
  lastName: string;
  mobiles: string[];
  needsVisaLetter: boolean;
  organization?: Organization;
  phones: string[];
  postalCode: string;
  state: string;
  title: string;
}

export interface EventNomination {
  contact: Contact;
  createdOn: string;
  event: MeetingEvent;
  id: number;
  role: string;
  status: string;
}
