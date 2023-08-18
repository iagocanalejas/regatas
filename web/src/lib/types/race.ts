import type { Trophy } from './trophy';
import type { Flag } from './flag';
import type { League } from './league';
import type { Entity } from './entity';
import type { Gender, RaceType } from './types';

export type Race = {
	id: number;
	name: string;

	day: number;
	date: string;
	type: RaceType;
	modality: string;

	trophy?: Trophy;
	flag?: Flag;
	league?: League;

	laps?: number;
	lanes?: number;
	cancelled: boolean;

	sponsor?: string;
	genders: Gender[];
};

export type RaceDetail = Race & {
	// participants: Participant[];
	series?: number;
	town?: string;
	organizer?: Entity;
};

export type RaceFilter = {
	trophy?: number;
	flag?: number;
	league?: number;
	participant?: number;
	year?: number;
	keywords?: string;
};

export type RaceSortBy = 'type' | 'date' | 'name' | 'league';
