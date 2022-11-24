import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ParticipantListComponent } from "./components/participant-list/participant-list.component";

const components = [
  ParticipantListComponent,
]

@NgModule({
  declarations: [
    ...components
  ],
  exports: [
    ...components
  ],
  imports: [
    CommonModule
  ]
})
export class ParticipantsModule {
}
