import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { participantSpeed, RaceDetail } from "src/types";

@Component({
  selector: 'race-detail-header',
  templateUrl: './race-detail-header.component.html',
  styleUrls: ['./race-detail-header.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RaceDetailHeaderComponent {
  // TODO: Show cancelled races
  @Input() race!: RaceDetail

  get winnerSpeed(): number {
    return participantSpeed(this.race.winner, this.race.distance);
  }
}
