import { Trophy } from "./trophy";
import { Flag } from "./flag";
import { League } from "./league";
import { Participant } from "./participant";
import { Entity } from "./entity";
import { Gender, RaceType } from "./types";

export interface Race {
  id: number;
  type: RaceType;
  name: string; // computed
  day: number;
  date: string;
  cancelled: boolean;
  is_female: boolean; // computed
  trophy?: Trophy;
  trophy_edition?: number;
  flag?: Flag;
  flag_edition?: number;
  league?: League;
  gender?: Gender;
  sponsor?: string;
  laps?: number;
  lanes?: number;
}

export interface RaceDetail extends Race {
  participants: Participant[];
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
