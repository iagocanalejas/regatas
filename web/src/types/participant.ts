import { Entity } from "./entity";
import * as moment from "moment";
import { TIME_FORMAT } from "./index";

export interface Penalty {
  penalty: number;
  disqualification: boolean;
  reason?: string;
}

export interface Participant {
  id: number;
  club: Entity;
  club_name?: string; // only exist if we have a computed name (ex: Puebla "B")
  laps: string[];
  times_per_lap: string[]; // computed
  time: string; // computed
  lane: number;
  series: number;
  disqualified: boolean;
  penalties: Penalty[];
}

const timeReg = /^[0-9]{2}:[0-9]{2}.[0-9]*$/;

export function participantSpeed(participant: Participant, distance: number): number {
  if (!timeReg.test(participant.time)) return 0

  moment.locale("es");
  const time = moment(participant.time, TIME_FORMAT)

  const seconds = time.minutes() * 60 + time.seconds();
  const mS = distance / seconds;
  return mS * 3.6; // kmH
}

export function compareParticipantTimes(p1: Participant, p2: Participant, ignoreDisqualifications: boolean = false): number {
  if (!ignoreDisqualifications && p1.disqualified) return 100
  if (!ignoreDisqualifications && p2.disqualified) return -100
  return moment(p1.time, TIME_FORMAT).diff(moment(p2.time, TIME_FORMAT))
}
