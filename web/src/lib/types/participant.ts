import type { Entity } from './entity';
import type { RaceFilter, RaceSortBy } from './race';
import type { Gender, ParticipantCategory, PenaltyReason } from './types';

export type Penalty = {
	penalty: number;
	disqualification: boolean;
	reason?: PenaltyReason;
};

export type Participant = {
	id: number;
	laps: string[];
	lane: number;
	series: number;
	distance: number;
	gender: Gender;
	category: ParticipantCategory;
	club: Entity;
	disqualified: boolean;
	penalties: Penalty[];
};

export type ParticipantFilter = Omit<RaceFilter, 'participant'> & {
	gender?: string;
	category?: string;
};

export type ParticipantSortBy = RaceSortBy | 'category' | 'speed';
