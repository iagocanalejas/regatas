import type { Trophy } from './trophy';
import type { Flag } from './flag';
import type { League } from './league';
import type { Gender, RaceType } from './types';
import type { Participant } from './participant';

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
	series?: number;
	cancelled: boolean;

	sponsor?: string;
	genders: Gender[];

	participants?: Participant[];
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
