import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { DEFAULT_PAGE_RESULT, Page, ParticipantUtils, Participation, Race, StringTypeUtils } from "src/types";

@Component({
  selector: 'participant-races',
  templateUrl: './participant-races.component.html',
  styleUrls: ['./participant-races.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ParticipantRacesComponent {
  @Input() participation: Page<Participation> = DEFAULT_PAGE_RESULT<Participation>();
  @Input() offset: number = 0;

  @Output() onRaceSelect: EventEmitter<Race> = new EventEmitter();

  selectRace(race: Race) {
    this.onRaceSelect.emit(race)
  }

  getParticipantSpeed(participation: Participation): number {
    return ParticipantUtils.speed(participation, participation.distance)
  }

  readableCategoryGender = StringTypeUtils.categoryGender;
  readableRaceType = StringTypeUtils.raceType;
  raceTypeIcon = (race: Race) => race.type === 'TIME_TRIAL' ? 'schedule' : 'more_vert';
}
