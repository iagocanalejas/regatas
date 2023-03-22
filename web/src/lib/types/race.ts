import type { Trophy } from './trophy';
import type { Flag } from './flag';
import type { League } from './league';
import type { Gender, RaceType } from './types';
import { z } from 'zod';

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

export const RaceFilter = z.object({
	trophy: z.optional(z.number().min(1)),
	flag: z.optional(z.number().min(1)),
	league: z.optional(z.number().min(1)),
	participant: z.optional(z.number().min(1)),
	year: z.optional(z.number().min(2003)),
	keywords: z.optional(z.string())
});
export type RaceFilter = z.infer<typeof RaceFilter>;

export type RaceSortBy = 'type' | 'date' | 'name' | 'league';
