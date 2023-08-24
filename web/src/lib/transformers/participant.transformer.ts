import { LAP_FORMAT, NO_TIME, TIME_FORMAT, type Participant } from '$lib/types';
import dayjs from 'dayjs';

export class ParticipantTransformer {
	static transformParticipants(participants: Participant[]): Participant[] {
		this.fillMissingLaps(participants);

		return participants.map((p) => this.transformParticipant(p));
	}

	static transformParticipant(participant: Participant): Participant {
		const laps = participant.laps.map((l) => this.parseLap(l).valueOf());
		// compute 'times_per_lap'
		participant.times_per_lap = laps.map((lap, itx) => {
			if (!lap || (itx > 0 && !laps[itx - 1])) return NO_TIME;
			return dayjs(lap - (itx > 0 ? laps[itx - 1] : 0)).format(LAP_FORMAT);
		});
		// format 'laps' and 'time'
		participant.raw_time = participant.laps.length ? this.formatTime([...participant.laps.slice(-1)][0]) : '00:00.000';
		participant.laps = participant.laps.slice(0, -1).map((l) => this.formatLap(l));
		return participant;
	}

	private static parseLap(lap: string): dayjs.Dayjs {
		return lap.includes('.') ? dayjs(lap + '0', 'hh:mm:ss.SS') : dayjs(lap, 'hh:mm:ss');
	}

	private static formatLap(lap: string): string {
		if (lap === NO_TIME) return lap;
		return this.parseLap(lap).format(LAP_FORMAT);
	}

	private static formatTime(time: string): string {
		if (time === NO_TIME) return time;
		return this.parseLap(time).format(TIME_FORMAT);
	}

	private static fillMissingLaps(participants: Participant[]) {
		const numberOfLaps = Math.max(...participants.map((p) => p.laps.length));
		const participantsMissingLaps = participants.filter((p) => p.laps.length !== numberOfLaps);
		if (participantsMissingLaps.length) {
			// check if there are any participants with missing laps
			const participantsAllLaps = participants.filter((p) => p.laps.length === numberOfLaps).map((p) => p.laps);
			const lapsOptions: number[][] = [];
			for (let i = 0; i < numberOfLaps; i++) {
				// compute a list of valid minutes for each lap
				lapsOptions.push(
					participantsAllLaps
						.map((l) => dayjs(l[i], 'hh:mm:ss.SS').minute())
						.filter((value, index, self) => self.indexOf(value) === index)
				);
			}

			participantsMissingLaps.forEach((participant) => {
				// for each participant without all the laps, fill in the missing ones with '---'
				const completedLaps = [];
				for (let i = 0, j = 0; i < numberOfLaps; i++) {
					if (lapsOptions[i].includes(dayjs(participant.laps[j], 'hh:mm:ss.SS').minute())) {
						completedLaps.push(participant.laps[j]);
						j++;
					} else {
						completedLaps.push(NO_TIME);
					}
				}
				participant.laps = completedLaps;
			});
		}
	}
}
