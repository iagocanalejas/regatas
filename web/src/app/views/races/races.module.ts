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
import { FormsModule } from "@angular/forms";
import { PaginationModule } from "../../shared/components/pagination/pagination.module";
import { DropdownModule } from "../../shared/components/dropdown/dropdown.module";
import { RaceListComponent } from "./components/race-list/race-list.component";
import { SearchBarModule } from "../../shared/components/search-bar/search-bar.module";
import { EmptyViewModule } from "../../shared/components/empty-view/empty-view.module";


@NgModule({
  declarations: [
    RacesComponent,
    RaceFiltersComponent,
    RaceListComponent,
  ],
  imports: [
    FormsModule, CommonModule,
    PaginationModule, DropdownModule, SearchBarModule, EmptyViewModule,
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
