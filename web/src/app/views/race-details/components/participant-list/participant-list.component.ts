import { ChangeDetectionStrategy, Component, Input, OnChanges, OnInit, SimpleChanges } from '@angular/core';
import { LAP_FORMAT, NO_TIME, Participant, ParticipantUtils, TIME_FORMAT } from "src/types";
import { NG_IF, ROTATE } from "src/app/shared/animations";
import * as dayjs from "dayjs";

@Component({
  selector: 'participant-list',
  templateUrl: './participant-list.component.html',
  styleUrls: ['./participant-list.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  animations: [...ROTATE, ...NG_IF],
})
export class ParticipantListComponent implements OnInit, OnChanges {
  @Input() participants!: Participant[];
  @Input() title!: string;
  @Input() headColumn!: string;
  @Input() distance?: number;
  @Input() collapsed: boolean = false;
  @Input() showDifference: boolean = false;

  showPerLapTimes: boolean = false;
  hasPenalties: boolean = false;
  ignorePenalties: boolean = false;

  winner!: Participant
  numberOfLaps: number[] = []
  fastestTurn: string[] = [];
  fastestLap: string[] = [];

  private init() {
    this.fastestTurn = this.numberOfLaps.map(current =>
      this.fastest(this.participants.map(p => p.laps[current])));
    this.fastestLap = this.numberOfLaps.map(current =>
      this.fastest(this.participants.map(p => p.times_per_lap[current])));

    this.winner = [...this.participants].sort((p1, p2) => ParticipantUtils.compareTimes(p1, p2))[0];
    this.numberOfLaps = Array.from(Array(Math.max(...this.participants.map(x => x.laps.length))).keys());
    this.hasPenalties = this.participants.some(x => x.penalties.length);
  }

  ngOnInit() {
    this.init()
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes['participants']) {
      this.init()
    }
  }

  get cardTitle(): string {
    return this.distance ? `${this.title} (${this.distance}m)` : this.title
  }

  get visibleLaps(): number[] {
    return this.showPerLapTimes ? this.numberOfLaps : this.numberOfLaps.slice(0, -1);
  }

  get displayedParticipants(): Participant[] {
    return this.ignorePenalties
      ? [...this.participants].sort((p1, p2) => ParticipantUtils.compareTimes(p1, p2, true))
      : this.participants;
  }

  get penaltiesButtonTooltip(): string {
    return this.ignorePenalties ? 'Aplicar penalizaciones' : 'Ignorar penalizaciones'
  }

  get lapModeButtonTooltip(): string {
    return this.showPerLapTimes ? 'Tiempos globales' : 'Tiempos por vuelta'
  }

  getLaps(participant: Participant): string[] {
    return this.showPerLapTimes ? participant.times_per_lap : participant.laps;
  }

  getTime(participant: Participant): string {
    return ParticipantUtils.time(participant, this.ignorePenalties)
  }

  getDifferenceTime(participant: Participant): string {
    if (!this.ignorePenalties && participant.disqualified) return 'DESCALIFICADO'
    const diff = dayjs(participant.time, TIME_FORMAT).diff(dayjs(this.winner.time, TIME_FORMAT));
    const duration = dayjs.duration({ milliseconds: diff });
    return dayjs(duration.asMilliseconds()).format(TIME_FORMAT);
  }

  getParticipantSpeed(participant: Participant): number {
    if (!this.distance) return 0  // should never happen
    return ParticipantUtils.speed(participant, this.distance);
  }

  isFastestLap(lap: number, time: string): boolean {
    return this.showPerLapTimes ? this.fastestLap[lap] === time : this.fastestTurn[lap] === time;
  }

  isFastestTime(time: string): boolean {
    return this.winner.time === time;
  }

  private fastest(values: string[]): string {
    return values.sort((a, b) => {
      if (a === NO_TIME) return 100
      if (b === NO_TIME) return -100
      return dayjs(a, LAP_FORMAT).diff(dayjs(b, LAP_FORMAT))
    })[0];
  }
}
