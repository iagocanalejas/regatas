import { Trophy } from "./trophy";
import { Flag } from "./flag";
import { League } from "./league";
import { Participant } from "./participant";
import { Entity } from "./entity";
import { Gender, RaceType } from "./types";

export type Race = {
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

export type RaceDetail = Race & {
  participants: Participant[];
  series?: number;
  town?: string;
  organizer?: Entity;
}

export type RaceFilter = {
  trophy?: number;
  flag?: number;
  league?: number;
  participant?: number;
  year?: number;
  keywords?: string;
}

export type RaceSortBy = 'type' | 'date' | 'name' | 'league' ;
