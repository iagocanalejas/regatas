import { Entity } from "./entity";
import * as moment from "moment";
import { TIME_FORMAT } from "./index";
import { Gender, ParticipantCategory, PenaltyReason } from "./types";

export interface Penalty {
  penalty: number;
  disqualification: boolean;
  reason?: PenaltyReason;
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
  hast_time_penalty: boolean; // computed
  penalties: Penalty[];
  gender: Gender;
  category: ParticipantCategory;
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

export function participantTime(participant: Participant, ignorePenalties: boolean = false): string {
  if (!ignorePenalties) return participant.time

  const penalties = participant.penalties.filter(p => !p.disqualification).reduce((prev, curr) => prev + curr.penalty, 0);
  return moment(participant.time, TIME_FORMAT).subtract(penalties, "seconds").format(TIME_FORMAT)
}

export function compareParticipantTimes(p1: Participant, p2: Participant, ignorePenalties: boolean = false): number {
  if (!ignorePenalties && p1.disqualified) return 100
  if (!ignorePenalties && p2.disqualified) return -100
  return moment(participantTime(p1, ignorePenalties), TIME_FORMAT).diff(moment(participantTime(p2, ignorePenalties), TIME_FORMAT))
}

