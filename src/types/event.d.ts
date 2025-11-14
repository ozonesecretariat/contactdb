import type { Country } from "./country";

export interface MeetingEvent {
  code: string;
  dates: string;
  dsa: string;
  endDate: string;
  startDate: string;
  termExp: string;
  title: string;
  venueCity: string;
  venueCountry: Country | null;
}
