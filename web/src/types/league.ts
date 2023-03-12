import { Gender } from "./types";

export interface League {
  id: number;
  name: string;
  symbol: string;
  gender: Gender;
}
