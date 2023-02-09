import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from "@angular/forms";
import { RouterModule } from "@angular/router";
import { routes } from "./club-details.routes";
import { StoreModule } from "@ngrx/store";
import { EffectsModule } from "@ngrx/effects";
import { ClubDetailsEffects } from "./reducers/club-details.effects";
import { featureKey } from "./reducers/club-details.reducers";
import { FEATURE_REDUCER_TOKEN } from "./reducers";
import { RaceListModule } from "../../shared/components/lists/race-list/race-list.module";
import { PaginationModule } from "../../shared/components/pagination/pagination.module";
import { ClubDetailsComponent } from "./components/club-details.component";
import { ClubDetailsService } from "./club-details.service";


@NgModule({
  declarations: [
    ClubDetailsComponent
  ],
  imports: [
    FormsModule, CommonModule,
    RaceListModule, PaginationModule,
    RouterModule.forChild(routes),
    StoreModule.forFeature(featureKey, FEATURE_REDUCER_TOKEN),
    EffectsModule.forFeature([ClubDetailsEffects]),
  ],
  providers: [
    ClubDetailsService
  ]
})
export class ClubDetailsModule {
}
