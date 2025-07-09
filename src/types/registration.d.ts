import type { MeetingEvent } from "src/types/event";
import type { Contact } from "src/types/nomination";
import type { Organization } from "src/types/organization";

export interface Registration {
  contact: Contact;
  createdAt: null | string;
  department: string;
  designation: string;
  event: MeetingEvent;
  id: number;
  organization: null | Organization;
  role: string;
  status: "Accredited" | "Nominated" | "Registered" | "Revoked";
}
