import { ChangeDetectionStrategy, Component, Input } from "@angular/core";
import { Club } from "src/types";

@Component({
  selector: 'club-card',
  templateUrl: './club-card.component.html',
  styleUrls: ['./club-card.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ClubCardComponent {
  @Input() club!: Club
}
