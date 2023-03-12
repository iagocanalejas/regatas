import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { participantSpeed, Participation, Race, readableCategoryGender } from "src/types";

@Component({
  selector: 'participant-races',
  templateUrl: './participant-races.component.html',
  styleUrls: ['./participant-races.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ParticipantRacesComponent {
  @Input() participation: Participation[] = [];

  @Output() onRaceSelect: EventEmitter<Race> = new EventEmitter();

  selectRace(race: Race) {
    this.onRaceSelect.emit(race)
  }

  getParticipantSpeed(participation: Participation): number {
    return participantSpeed(participation, participation.distance)
  }

  readableCategoryGender = readableCategoryGender
}
