import { League } from "./league";
import { Trophy } from "./trophy";
import { Flag } from "./flag";
import { Participant, ParticipantFilter, ParticipantSortBy, ParticipantUtils, Participation, Penalty } from "./participant";
import { Club, ClubDetail, Organizers } from "./entity";
import { Race, RaceDetail, RaceFilter, RaceSortBy } from "./race";
import { DEFAULT_PAGE, DEFAULT_PAGE_RESULT, Page, PaginationConfig } from "./page";
import {
  category_es,
  categoryGender_es,
  Gender,
  gender_es,
  GENDERS,
  PARTICIPANT_CATEGORIES,
  ParticipantCategory,
  PenaltyReason,
  penaltyReason_es,
  RaceType,
  raceType_es
} from "./types";

// TODO: .SS format is currently broken
// https://github.com/iamkun/dayjs/issues/1331
// https://github.com/iamkun/dayjs/pull/1914
export const TIME_FORMAT = 'mm:ss.SSS';
export const LAP_FORMAT = 'mm:ss';
export const NO_TIME = '- - - - -';

export {
  Page, PaginationConfig,
  RaceType, Gender, PenaltyReason, ParticipantCategory, GENDERS, PARTICIPANT_CATEGORIES,
  League, Flag, Trophy,
  Club, ClubDetail, Organizers,
  Race, RaceDetail, RaceFilter, RaceSortBy,
  Participation, Participant, ParticipantFilter, ParticipantSortBy, Penalty,
  ParticipantUtils, raceType_es, penaltyReason_es, gender_es, category_es, categoryGender_es,
  DEFAULT_PAGE, DEFAULT_PAGE_RESULT
}
