import { Gender, League } from "./league";
import { Trophy } from "./trophy";
import { Flag } from "./flag";
import { compareParticipantTimes, Participant, participantSpeed } from "./participant";
import { Club, ClubDetail, Organizers } from "./entity";
import { Race, RaceDetail, RaceFilter } from "./race";
import { Request, RequestChange, RequestModel, RequestType } from "./requests";
import { DEFAULT_PAGE, DEFAULT_PAGE_RESULT, Page, PaginationConfig } from "./page";

export const TIME_FORMAT = 'mm:ss.SS';
export const LAP_FORMAT = 'mm:ss';
export const NO_TIME = '- - - - -';

export {
  Page, PaginationConfig, Gender,
  League, Flag, Trophy,
  Club, ClubDetail, Organizers,
  Race, RaceFilter, RaceDetail,
  RequestType, RequestModel, RequestChange, Request,
  Participant, participantSpeed, compareParticipantTimes,
  DEFAULT_PAGE, DEFAULT_PAGE_RESULT
}
