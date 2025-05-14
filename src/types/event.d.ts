import type { Country } from "./country";

export interface MeetingEvent {
  code: string;
  dates: string;
  endDate: string;
  startDate: string;
  title: string;
  venueCity: string;
  venueCountry: Country;
}
