import type { League } from './league';
import type { Trophy } from './trophy';
import type { Flag } from './flag';
import type { Entity } from './entity';
import type { AssociatedRace, Race, RaceDatasource, RaceFilter, RaceSortBy } from './race';
import { type Participant, type ParticipantFilter, type ParticipantSortBy, ParticipantUtils } from './participant';
import { DEFAULT_PAGE, DEFAULT_PAGE_RESULT, type Page, type PaginationConfig, type PaginationResult } from './page';
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

import dayjs from 'dayjs';
import 'dayjs/locale/es';
import customParseFormat from 'dayjs/plugin/customParseFormat';
import duration from 'dayjs/plugin/duration';
dayjs.locale('es');
dayjs.extend(customParseFormat);
dayjs.extend(duration);

// TODO: .SS format is currently broken
// https://github.com/iamkun/dayjs/issues/1331
// https://github.com/iamkun/dayjs/pull/1914
export const TIME_FORMAT = 'mm:ss.SSS';
export const LAP_FORMAT = 'mm:ss';
export const NO_TIME = '- - - - -';

export {
	Page,
	PaginationConfig,
	PaginationResult,
	RaceType,
	Gender,
	PenaltyReason,
	ParticipantCategory,
	GENDERS,
	PARTICIPANT_CATEGORIES,
	League,
	Flag,
	Trophy,
	Entity,
	AssociatedRace,
	Race,
	RaceDatasource,
	RaceFilter,
	RaceSortBy,
	Participant,
	ParticipantFilter,
	ParticipantSortBy,
	raceType_es,
	penaltyReason_es,
	gender_es,
	category_es,
	categoryGender_es,
	DEFAULT_PAGE,
	DEFAULT_PAGE_RESULT,
	ParticipantUtils
};
