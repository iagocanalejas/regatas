import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from "@angular/forms";
import { SharedModule } from "../../shared/shared.module";
import { ClubsComponent } from "./components/clubs.component";
import { RouterModule } from "@angular/router";
import { routes } from "./clubs.routes";
import { ClubsService } from "./clubs.service";
import { StoreModule } from "@ngrx/store";
import { EffectsModule } from "@ngrx/effects";
import { ClubsEffects } from "./reducers/clubs.effects";
import { featureKey } from "./reducers/clubs.reducers";
import { FEATURE_REDUCER_TOKEN } from "./reducers";
import { ClubCardComponent } from "./components/card/club-card.component";
import { ClubDetailsComponent } from "./components/details/club-details.component";


@NgModule({
  declarations: [
    ClubsComponent,
    ClubDetailsComponent,
    ClubCardComponent,
  ],
  imports: [
    FormsModule, CommonModule,
    SharedModule,
    RouterModule.forChild(routes),
    StoreModule.forFeature(featureKey, FEATURE_REDUCER_TOKEN),
    EffectsModule.forFeature([ClubsEffects]),
  ],
  providers: [
    ClubsService
  ]
})
export class ClubsModule {
}
