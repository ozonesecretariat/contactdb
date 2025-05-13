import type { Country } from "./country";

export interface MeetingEvent {
  code: string;
  title: string;
  startDate: string;
  endDate: string;
  venueCountry: Country;
  venueCity: string;
  dates: string;
}
