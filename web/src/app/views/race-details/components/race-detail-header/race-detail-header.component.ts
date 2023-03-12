import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { Participant, ParticipantUtils, RaceDetail } from "src/types";

@Component({
  selector: 'race-detail-header',
  templateUrl: './race-detail-header.component.html',
  styleUrls: ['./race-detail-header.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RaceDetailHeaderComponent {
  // TODO: Show cancelled races
  @Input() race!: RaceDetail
  @Input() winner?: Participant

  get winnerSpeed(): number {
    if (!this.winner) return 0
    return ParticipantUtils.speed(this.winner, this.winner.distance);
  }
}
