import { ChangeDetectionStrategy, Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { compareParticipantTimes, NO_TIME, Participant, participantSpeed, TIME_FORMAT } from "src/types";
import { NG_IF, ROTATE } from "src/app/shared/animations";
import * as moment from "moment";

@Component({
  selector: 'participant-list',
  templateUrl: './participant-list.component.html',
  styleUrls: ['./participant-list.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  animations: [...ROTATE, ...NG_IF],
})
export class ParticipantListComponent implements OnChanges {
  @Input() participants!: Participant[];
  @Input() title!: string;
  @Input() headColumn!: string;
  @Input() distance!: number;
  @Input() collapsed: boolean = false;
  @Input() showDifference: boolean = false;

  showPerLapTimes: boolean = false;
  ignoreDisqualifications: boolean = false;

  fastestTurn: string[] = [];
  fastestLap: string[] = [];

  ngOnChanges(changes: SimpleChanges) {
    if (changes['participants']) {
      this.fastestTurn = this.numberOfLaps.map(current =>
        this.fastest(this.participants.map(p => p.laps[current])));
      this.fastestLap = this.numberOfLaps.map(current =>
        this.fastest(this.participants.map(p => p.times_per_lap[current])));
    }
  }

  get numberOfLaps(): number[] {
    const max = Math.max(...this.participants.map(x => x.laps.length));
    return Array.from(Array(max).keys());
  }

  get visibleLaps(): number[] {
    return this.showPerLapTimes ? this.numberOfLaps : this.numberOfLaps.slice(0, -1);
  }

  get winner(): Participant {
    return [...this.participants].sort(
      (p1, p2) => compareParticipantTimes(p1, p2))[0];
  }

  get hasDisqualifications(): boolean {
    return this.participants.some(x => x.disqualified)
  }

  get displayedParticipants(): Participant[] {
    return this.ignoreDisqualifications
      ? [...this.participants].sort((p1, p2) => compareParticipantTimes(p1, p2, true))
      : this.participants;
  }

  getLaps(participant: Participant): string[] {
    return this.showPerLapTimes ? participant.times_per_lap : participant.laps;
  }

  getDifferenceTime(participant: Participant): string {
    if (!this.ignoreDisqualifications && participant.disqualified) return 'DESCALIFICADO'
    const diff = moment(participant.time, TIME_FORMAT).diff(moment(this.winner.time, TIME_FORMAT));
    const duration = moment.duration(diff, 'milliseconds');
    return moment.utc(duration.asMilliseconds()).format(TIME_FORMAT);
  }

  getParticipantSpeed(participant: Participant): number {
    return participantSpeed(participant, this.distance);
  }

  isFastestLap(lap: number, time: string): boolean {
    return this.showPerLapTimes ? this.fastestLap[lap] === time : this.fastestTurn[lap] === time;
  }

  isFastestTime(time: string): boolean {
    return this.winner.time === time;
  }

  toggleTable() {
    this.collapsed = !this.collapsed;
  }

  togglePerLapMode() {
    this.showPerLapTimes = !this.showPerLapTimes;
  }

  toggleDisqualification() {
    this.ignoreDisqualifications = !this.ignoreDisqualifications;
  }

  private fastest(values: string[]): string {
    return values.sort((a, b) => {
      if (a === NO_TIME) return 100
      if (b === NO_TIME) return -100
      return moment(a, TIME_FORMAT).diff(moment(b, TIME_FORMAT))
    })[0];
  }
}
