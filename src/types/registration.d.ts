import type { MeetingEvent } from "./event";
import type { Organization } from "./organization";

export interface Contact {
  emailCcs: string[];
  emails: string[];
  firstName: string;
  fullName: string;
  id: number;
  lastName: string;
  mobiles: string[];
  organization?: Organization;
  phones: string[];
}

export interface EventNomination {
  contact: Contact;
  createdOn: string;
  event: MeetingEvent;
  id: number;
  status: string;
}
