import { compareParticipantTimes, LAP_FORMAT, NO_TIME, Participant, TIME_FORMAT } from "src/types";
import * as moment from "moment/moment";

export class ParticipantTransformer {
  static transformParticipants(participants: Participant[]): Participant[] {
    moment.locale("es");

    this.fillMissingLaps(participants);

    return participants
      .map(p => this.transformParticipant(p))
      .sort((p1, p2) => compareParticipantTimes(p1, p2))
  }

  static transformParticipant(participant: Participant): Participant {
    moment.locale("es");

    const laps = participant.laps.map(l => moment(l, 'hh:mm:ss.SS').valueOf());
    // compute 'times_per_lap'
    participant.times_per_lap = laps.map((lap, itx) => {
      if (!lap || (itx > 0 && !laps[itx - 1])) return NO_TIME
      return moment.utc(lap - ((itx > 0) ? laps[itx - 1] : 0)).format(LAP_FORMAT)
    })
    // format 'laps' and 'time'
    participant.time = this.formatTime([...participant.laps.slice(-1)][0]);
    participant.laps = participant.laps.map(l => this.formatLap(l));
    participant.hast_time_penalty = participant.penalties.some(p => !p.disqualification);
    return participant;
  }

  private static formatLap(lap: string): string {
    if (lap === NO_TIME) return lap;
    return moment(lap, 'hh:mm:ss.SS').format(LAP_FORMAT)
  }

  private static formatTime(time: string): string {
    if (time === NO_TIME) return time;
    return moment(time, 'hh:mm:ss.SS').format(TIME_FORMAT)
  }

  private static fillMissingLaps(participants: Participant[]) {
    const numberOfLaps = Math.max(...participants.map(p => p.laps.length));
    const participantsMissingLaps = participants.filter(p => p.laps.length !== numberOfLaps);
    if (participantsMissingLaps.length) { // check if there are any participants with missing laps
      const participantsAllLaps = participants.filter(p => p.laps.length === numberOfLaps).map(p => p.laps);
      const lapsOptions: number[][] = []
      for (let i = 0; i < numberOfLaps; i++) { // compute a list of valid minutes for each lap
        lapsOptions.push(
          participantsAllLaps
            .map(l => moment(l[i], 'hh:mm:ss.SS').minutes())
            .filter((value, index, self) => self.indexOf(value) === index)
        );
      }

      participantsMissingLaps.forEach(participant => { // for each participant without all the laps, fill in the missing ones with '---'
        const completedLaps = [];
        for (let i = 0, j = 0; i < numberOfLaps; i++) {
          if (lapsOptions[i].includes(moment(participant.laps[j], 'hh:mm:ss.SS').minutes())) {
            completedLaps.push(participant.laps[j]);
            j++;
          } else {
            completedLaps.push(NO_TIME);
          }
        }
        participant.laps = completedLaps;
      })
    }
  }
}
