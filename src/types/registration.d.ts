import type { Country } from "src/types/country";
import type { EncryptedFile } from "src/types/encryptedFile";
import type { MeetingEvent } from "src/types/event";
import type { Contact } from "src/types/nomination";
import type { Organization } from "src/types/organization";

export interface DSA {
  arrivalDate: string;
  boardingPass: EncryptedFile | null;
  bp: string;
  cashCard: string;
  departureDate: string;
  dsaOnArrival: number;
  id: number;
  numberOfDays: number;
  paidDsa: boolean;
  passport: EncryptedFile | null;
  signature: EncryptedFile | null;
  totalDsa: string;
  umojaTravel: string;
}

export interface Registration {
  contact: Contact;
  createdAt: null | string;
  department: string;
  designation: string;
  dsa?: DSA;
  dsaCountry?: Country;
  event: MeetingEvent;
  id: number;
  organization: null | Organization;
  role: string;
  status: "Accredited" | "Nominated" | "Registered" | "Revoked";
  tags: string[];
}

export interface RegistrationTag {
  name: string;
}
