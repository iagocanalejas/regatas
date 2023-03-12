import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { DEFAULT_PAGE_RESULT, Page, Race } from "src/types";

@Component({
  selector: 'race-list',
  templateUrl: './race-list.component.html',
  styleUrls: ['./race-list.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class RaceListComponent {
  @Input() races: Page<Race> = DEFAULT_PAGE_RESULT<Race>();
  @Input() offset: number = 0;

  @Output() onRaceSelect: EventEmitter<Race> = new EventEmitter();

  selectRace(race: Race) {
    this.onRaceSelect.emit(race)
  }
}
