import { League } from "./league";
import { Participation } from "./participant";

export interface Entity {
  id: number;
  name: string;
}

export interface Club extends Entity {
}

export interface ClubDetail extends Club {
  participation: Participation[]
}

export interface Organizers {
  clubs: Club[];
  leagues: League[];
  federations: Entity[];
  private: Entity[];
}
