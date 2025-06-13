import type { MeetingEvent } from "./event";
import type { Organization } from "./organization";

export interface Contact {
  emails: string[];
  firstName: string;
  fullName: string;
  id: number;
  lastName: string;
  organization?: Organization;
}

export interface EventNomination {
  contact: Contact;
  createdOn: string;
  event: MeetingEvent;
  id: number;
  status: string;
}
