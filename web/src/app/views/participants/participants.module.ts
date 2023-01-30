import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ParticipantListComponent } from "./components/participant-list/participant-list.component";
import { PenaltyListComponent } from "./components/penalty-list/penalty-list.component";
import { NgbTooltipModule } from "@ng-bootstrap/ng-bootstrap";

const components = [
  ParticipantListComponent,
  PenaltyListComponent,
]

@NgModule({
  declarations: [
    ...components
  ],
  exports: [
    ...components
  ],
  imports: [
    CommonModule, NgbTooltipModule
  ]
})
export class ParticipantsModule {
}
