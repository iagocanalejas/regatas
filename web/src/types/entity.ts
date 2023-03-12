import { League } from "./league";
import { Participation } from "./participant";

export type Entity = {
  id: number;
  name: string;
}
export type Club = Entity

export type ClubDetail = Club & {
  participation: Participation[];
}
export type Organizers = {
  clubs: Club[];
  leagues: League[];
  federations: Entity[];
  private: Entity[];
}
