import { League } from "./league";
import { Trophy } from "./trophy";
import { Flag } from "./flag";
import { compareParticipantTimes, Participant, participantSpeed, participantTime, Penalty } from "./participant";
import { Club, ClubDetail, Organizers } from "./entity";
import { Race, RaceDetail, RaceFilter } from "./race";
import { Request, RequestChange, RequestModel, RequestType } from "./requests";
import { DEFAULT_PAGE, DEFAULT_PAGE_RESULT, Page, PaginationConfig } from "./page";
import { Gender, ParticipantCategory, PenaltyReason, RaceType, readableCategory, readableReason, readableGender } from "./types";

export const TIME_FORMAT = 'mm:ss.SS';
export const LAP_FORMAT = 'mm:ss';
export const NO_TIME = '- - - - -';

export {
  Page, PaginationConfig,
  RaceType, Gender, PenaltyReason, ParticipantCategory,
  League, Flag, Trophy,
  Club, ClubDetail, Organizers,
  Race, RaceFilter, RaceDetail,
  Participant, Penalty,
  RequestType, RequestModel, RequestChange, Request,
  participantSpeed, participantTime, compareParticipantTimes,
  readableReason, readableCategory, readableGender,
  DEFAULT_PAGE, DEFAULT_PAGE_RESULT
}
