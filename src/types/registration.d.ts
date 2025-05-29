import type { MeetingEvent } from "./event";
import type { Organization } from "./organization";

export interface Contact {
  id: number;
  firstName: string;
  lastName: string;
  emails: string[];
}

export interface EventNomination {
  id: number;
  event: MeetingEvent;
  organization: Organization;
  contact: Contact;
  createdOn: string;
  status: string;
}