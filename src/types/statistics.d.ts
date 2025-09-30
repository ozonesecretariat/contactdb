export interface EventCount {
  count: number;
  gender: string;
  organizationType: string;
  region: string;
  role: string;
  status: string;
  subregion: string;
}

export interface Statistics {
  registrations: EventCount[];
  schema: {
    gender: string[];
    organizationType: string[];
    region: string[];
    role: string[];
    status: string[];
    subregion: string[];
  };
}
