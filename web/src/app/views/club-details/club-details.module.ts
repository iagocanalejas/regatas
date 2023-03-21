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
import { PaginationModule } from "../../shared/components/pagination/pagination.module";
import { ClubDetailsComponent } from "./components/club-details.component";
import { ClubDetailsService } from "./club-details.service";
import { ParticipantRacesComponent } from "./components/participant-races/participant-races.component";
import { NgbTooltipModule } from "@ng-bootstrap/ng-bootstrap";
import { DropdownModule } from "../../shared/components/dropdown/dropdown.module";
import { ParticipantRaceFiltersComponent } from "./components/participant-race-filters/participant-race-filters.component";
import { SearchBarModule } from "../../shared/components/search-bar/search-bar.module";
import { EmptyViewModule } from "../../shared/components/empty-view/empty-view.module";


@NgModule({
  declarations: [
    ClubDetailsComponent,
    ParticipantRacesComponent,
    ParticipantRaceFiltersComponent,
  ],
  imports: [
    FormsModule, CommonModule, NgbTooltipModule,
    PaginationModule, DropdownModule, SearchBarModule, EmptyViewModule,
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
