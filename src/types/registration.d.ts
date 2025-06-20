import type { MeetingEvent } from "./event";
import type { Organization } from "./organization";

export interface Contact {
  department: string;
  designation: string;
  emailCcs: string[];
  emails: string[];
  firstName: string;
  fullName: string;
  id: number;
  lastName: string;
  mobiles: string[];
  organization?: Organization;
  phones: string[];
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
