import type { League } from './league';
import type { Trophy } from './trophy';
import type { Flag } from './flag';
import type { Club, ClubDetail, Organizers } from './entity';
import type { Race, RaceDetail, RaceFilter, RaceSortBy } from './race';
import { DEFAULT_PAGE, DEFAULT_PAGE_RESULT, type Page, type PaginationConfig } from './page';
import {
	category_es,
	categoryGender_es,
	type Gender,
	gender_es,
	GENDERS,
	PARTICIPANT_CATEGORIES,
	type ParticipantCategory,
	type PenaltyReason,
	penaltyReason_es,
	type RaceType,
	raceType_es
} from './types';

// TODO: .SS format is currently broken
// https://github.com/iamkun/dayjs/issues/1331
// https://github.com/iamkun/dayjs/pull/1914
export const TIME_FORMAT = 'mm:ss.SSS';
export const LAP_FORMAT = 'mm:ss';
export const NO_TIME = '- - - - -';

export {
	Page,
	PaginationConfig,
	RaceType,
	Gender,
	PenaltyReason,
	ParticipantCategory,
	GENDERS,
	PARTICIPANT_CATEGORIES,
	League,
	Flag,
	Trophy,
	Club,
	ClubDetail,
	Organizers,
	Race,
	RaceDetail,
	RaceFilter,
	RaceSortBy,
	raceType_es,
	penaltyReason_es,
	gender_es,
	category_es,
	categoryGender_es,
	DEFAULT_PAGE,
	DEFAULT_PAGE_RESULT
};
