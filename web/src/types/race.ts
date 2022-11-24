import { Trophy } from "./trophy";
import { Flag } from "./flag";
import { League } from "./league";
import { Participant } from "./participant";
import { Entity } from "./entity";

export interface Race {
  id: number;
  type: 'TIME_TRIAL' | 'CONVENTIONAL';
  name: string; // computed
  modality: 'TRAINERA' | 'VETERAN';
  day: number;
  date: string;
  cancelled: boolean;
  is_female: boolean; // computed
  trophy?: Trophy;
  trophy_edition?: number;
  flag?: Flag;
  flag_edition?: number;
  league?: League;
  gender?: string;
  sponsor?: string;
}

export interface RaceDetail extends Race {
  participants: Participant[];
  distance: number;
  winner: Participant; // computed
  laps?: number;
  lanes?: number;
  series?: number;
  town?: string;
  organizer?: Entity;
}

export interface RaceFilter {
  trophy?: number;
  flag?: number;
  league?: number;
  participant_club?: number;
  year?: number;
  keywords?: string;
}
