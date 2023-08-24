import dayjs from 'dayjs';
import type { Entity } from './entity';
import type { RaceFilter, RaceSortBy } from './race';
import type { Gender, ParticipantCategory, PenaltyReason } from './types';
import { TIME_FORMAT } from '.';

export type Penalty = {
	penalty: number;
	disqualification: boolean;
	reason?: PenaltyReason;
};

export type Participant = {
	id: number;
	laps: string[];
	handicap?: string;
	lane: number;
	series: number;
	distance: number;
	gender: Gender;
	category: ParticipantCategory;
	club: Entity;
	disqualified: boolean;
	penalties: Penalty[];

	// computed
	raw_time: string;
	times_per_lap: string[];
};

export type ParticipantFilter = Omit<RaceFilter, 'participant'> & {
	gender?: string;
	category?: string;
};

export type ParticipantSortBy = RaceSortBy | 'category' | 'speed';

export class ParticipantUtils {
	private static timeReg = /^[0-9]{2}:[0-9]{2}.[0-9]*$/;

	static speed(participant: Participant, distance: number): number {
		if (!ParticipantUtils.timeReg.test(participant.raw_time)) return 0;

		const time = dayjs(participant.raw_time, TIME_FORMAT);
		if (!time.minute()) return 0;

		const seconds = time.minute() * 60 + time.second();
		const mS = distance / seconds;
		return mS * 3.6; // kmH
	}

	static time(participant: Participant): string {
		const penalties = participant.penalties
			.filter((p) => !p.disqualification)
			.reduce((prev, curr) => prev + curr.penalty, 0);

		let computedTime = dayjs(participant.raw_time, TIME_FORMAT).subtract(penalties, 'seconds');
		if (participant.handicap) {
			// TODO: add handicap
		}

		return computedTime.format(TIME_FORMAT);
	}
}
