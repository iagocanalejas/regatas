import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { DEFAULT_PAGE_RESULT, Page, Race, RaceSortBy } from "src/types";

@Component({
  selector: 'race-list',
  templateUrl: './race-list.component.html',
  styleUrls: ['./race-list.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class RaceListComponent {
  @Input() races: Page<Race> | null = DEFAULT_PAGE_RESULT<Race>();
  @Input() offset: number = 0;

  @Output() onRaceSelect: EventEmitter<Race> = new EventEmitter();
  @Output() onSortingChange = new EventEmitter<string>();

  sortBy: RaceSortBy = 'date'
  isAscSorting: boolean = true

  get sortIcon() {
    return this.isAscSorting ? 'north' : 'south'
  }

  selectRace(race: Race) {
    this.onRaceSelect.emit(race)
  }

  toggleSorting(key: RaceSortBy) {
    if (this.sortBy === key) {
      this.isAscSorting = !this.isAscSorting;
    } else {
      this.sortBy = key;
      this.isAscSorting = true;
    }
    this.onSortingChange.emit(`${this.isAscSorting ? '' : '-'}${this.sortBy}`)
  }
}
