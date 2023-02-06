import { Race } from "./race";
import { Page } from "./page";
import { League } from "./league";

export interface Entity {
  id: number;
  name: string;
}

export interface Club extends Entity {
}

export interface ClubDetail extends Club {
  races: Page<Race>
}

export interface Organizers {
  clubs: Club[];
  leagues: League[];
  federations: Entity[];
  private: Entity[];
}
