import type { MeetingEvent } from "./event";
import type { Organization } from "./organization";

export interface Contact {
  emails: string[];
  firstName: string;
  id: number;
  lastName: string;
}

export interface EventNomination {
  contact: Contact;
  createdOn: string;
  event: MeetingEvent;
  id: number;
  organization: Organization;
  status: string;
}
