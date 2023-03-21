import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import {
  categoryGender_es,
  DEFAULT_PAGE_RESULT,
  Page,
  ParticipantSortBy,
  ParticipantUtils,
  Participation,
  Race,
  RaceType,
  raceType_es
} from "src/types";

@Component({
  selector: 'participant-races',
  templateUrl: './participant-races.component.html',
  styleUrls: ['./participant-races.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ParticipantRacesComponent {
  @Input() participation: Page<Participation> | null = DEFAULT_PAGE_RESULT<Participation>();
  @Input() offset: number = 0;

  @Output() onRaceSelect: EventEmitter<Race> = new EventEmitter();
  @Output() onSortingChange = new EventEmitter<string>();

  sortBy: ParticipantSortBy = 'date'
  isAscSorting: boolean = true

  get sortIcon() {
    return this.isAscSorting ? 'north' : 'south'
  }

  selectRace(race: Race) {
    this.onRaceSelect.emit(race)
  }

  getParticipantSpeed(participation: Participation) {
    return ParticipantUtils.speed(participation, participation.distance)
  }

  toggleSorting(key: ParticipantSortBy) {
    if (this.sortBy === key) {
      this.isAscSorting = !this.isAscSorting;
    } else {
      this.sortBy = key;
      this.isAscSorting = true;
    }
    this.onSortingChange.emit(`${this.isAscSorting ? '' : '-'}${this.sortBy}`)
  }

  readableCategoryGender = categoryGender_es;
  readableRaceType = (e: RaceType) => raceType_es[e];
  raceTypeIcon = (race: Race) => race.type === 'TIME_TRIAL' ? 'schedule' : 'more_vert';
}
