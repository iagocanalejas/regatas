import { League } from "./league";
import { Trophy } from "./trophy";
import { Flag } from "./flag";
import { Participant, ParticipantUtils, Participation, Penalty } from "./participant";
import { Club, ClubDetail, Organizers } from "./entity";
import { Race, RaceDetail, RaceFilter } from "./race";
import { DEFAULT_PAGE, DEFAULT_PAGE_RESULT, Page, PaginationConfig } from "./page";
import { Gender, ParticipantCategory, PenaltyReason, RaceType, StringTypeUtils } from "./types";

// TODO: .SS format is currently broken
// https://github.com/iamkun/dayjs/issues/1331
// https://github.com/iamkun/dayjs/pull/1914
export const TIME_FORMAT = 'mm:ss.SSS';
export const LAP_FORMAT = 'mm:ss';
export const NO_TIME = '- - - - -';

export {
  Page, PaginationConfig,
  RaceType, Gender, PenaltyReason, ParticipantCategory,
  League, Flag, Trophy,
  Club, ClubDetail, Organizers,
  Race, RaceFilter, RaceDetail,
  Participation, Participant, Penalty,
  ParticipantUtils, StringTypeUtils,
  DEFAULT_PAGE, DEFAULT_PAGE_RESULT
}
