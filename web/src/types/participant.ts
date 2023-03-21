import { Entity } from "./entity";
import { Race, RaceFilter, TIME_FORMAT } from "./index";
import { Gender, ParticipantCategory, PenaltyReason } from "./types";
import * as dayjs from "dayjs";
import { RaceSortBy } from "./race";

export type Penalty = {
  penalty: number;
  disqualification: boolean;
  reason?: PenaltyReason;
}

export type Participation = {
  id: number;
  laps: string[];
  lane: number;
  series: number;
  distance: number;
  gender: Gender;
  category: ParticipantCategory;
  race: Race
  time: string; // computed
}

export type Participant = Omit<Participation, "race"> & {
  club: Entity;
  club_name?: string; // only exist if we have a computed name (ex: Puebla "B")
  times_per_lap: string[]; // computed
  disqualified: boolean;
  hast_time_penalty: boolean; // computed
  penalties: Penalty[];
}

export type ParticipantFilter = Omit<RaceFilter, "participant"> & {
  gender?: string;
  category?: string;
}

export type ParticipantSortBy = RaceSortBy | 'category' | 'speed' ;

export class ParticipantUtils {
  private static timeReg = /^[0-9]{2}:[0-9]{2}.[0-9]*$/;

  static speed(participant: Participant | Participation, distance: number) {
    if (!ParticipantUtils.timeReg.test(participant.time)) return 0

    const time = dayjs(participant.time, TIME_FORMAT)
    if (!time.minute()) return 0

    const seconds = time.minute() * 60 + time.second();
    const mS = distance / seconds;
    return mS * 3.6; // kmH
  }

  static time(participant: Participant, ignorePenalties: boolean = false) {
    if (!ignorePenalties) return participant.time

    const penalties = participant.penalties.filter(p => !p.disqualification).reduce((prev, curr) => prev + curr.penalty, 0);
    return dayjs(participant.time, TIME_FORMAT).subtract(penalties, "seconds").format(TIME_FORMAT)
  }

  static compareTimes(p1: Participant, p2: Participant, ignorePenalties: boolean = false) {
    if (!ignorePenalties && p1.disqualified) return 100
    if (!ignorePenalties && p2.disqualified) return -100

    return dayjs(ParticipantUtils.time(p1, ignorePenalties), TIME_FORMAT).diff(dayjs(ParticipantUtils.time(p2, ignorePenalties), TIME_FORMAT))
  }
}

