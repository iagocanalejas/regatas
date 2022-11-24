import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RacesComponent } from './components/races.component';
import { RouterModule } from "@angular/router";
import { routes } from "./races.routes";
import { StoreModule } from '@ngrx/store';
import { FEATURE_REDUCER_TOKEN } from './reducers';
import { RacesService } from "./races.service";
import { EffectsModule } from '@ngrx/effects';
import { RacesEffects } from './reducers/races.effects';
import { featureKey } from "./reducers/races.reducers";
import { RaceFiltersComponent } from './components/race-filters/race-filters.component';
import { SharedModule } from "src/app/shared/shared.module";
import { FormsModule } from "@angular/forms";
import { RaceDetailsComponent } from './components/details/race-details.component';
import { ParticipantsModule } from "../participants/participants.module";
import { RaceDetailHeaderComponent } from './components/details/race-detail-header/race-detail-header.component';


@NgModule({
  declarations: [
    RacesComponent,
    RaceFiltersComponent,
    RaceDetailsComponent,
    RaceDetailHeaderComponent,
  ],
  imports: [
    FormsModule, CommonModule,
    SharedModule, ParticipantsModule,
    RouterModule.forChild(routes),
    StoreModule.forFeature(featureKey, FEATURE_REDUCER_TOKEN),
    EffectsModule.forFeature([RacesEffects]),
  ],
  providers: [
    RacesService,
  ],
})
export class RacesModule {
}
