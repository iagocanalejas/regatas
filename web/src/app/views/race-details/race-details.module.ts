import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from "@angular/router";
import { routes } from "./race-details.routes";
import { StoreModule } from '@ngrx/store';
import { FEATURE_REDUCER_TOKEN } from './reducers';
import { EffectsModule } from '@ngrx/effects';
import { RaceDetailsEffects } from './reducers/race-details.effects';
import { featureKey } from "./reducers/race-details.reducers";
import { FormsModule } from "@angular/forms";
import { RaceDetailsComponent } from './components/race-details.component';
import { RaceDetailHeaderComponent } from './components/race-detail-header/race-detail-header.component';
import { RaceDetailsService } from "./race-details.service";
import { ParticipantListComponent } from "./components/participant-list/participant-list.component";
import { PenaltyListComponent } from "./components/penalty-list/penalty-list.component";
import { NgbTooltipModule } from "@ng-bootstrap/ng-bootstrap";


@NgModule({
  declarations: [
    RaceDetailsComponent,
    RaceDetailHeaderComponent,
    ParticipantListComponent,
    PenaltyListComponent,
  ],
  imports: [
    FormsModule, CommonModule, NgbTooltipModule,
    RouterModule.forChild(routes),
    StoreModule.forFeature(featureKey, FEATURE_REDUCER_TOKEN),
    EffectsModule.forFeature([RaceDetailsEffects]),
  ],
  providers: [
    RaceDetailsService,
  ],
})
export class RaceDetailsModule {
}
