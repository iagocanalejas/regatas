import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RaceListComponent } from "./race-list.component";

@NgModule({
  declarations: [
    RaceListComponent
  ],
  imports: [
    CommonModule,
  ],
  exports: [
    RaceListComponent,
  ],
})
export class RaceListModule {
}
