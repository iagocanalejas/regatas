import { RouterModule, Routes } from "@angular/router";
import { NgModule } from "@angular/core";

// @formatter:off
const APP_ROUTES: Routes = [
  { path: '', redirectTo: 'races', pathMatch: 'full' },
  { path: 'races', loadChildren: () => import('./views/races/races.module').then(m => m.RacesModule) },
  { path: 'races/:race_id', loadChildren: () => import('./views/race-details/race-details.module').then(m => m.RaceDetailsModule) },
  { path: 'clubs', loadChildren: () => import('./views/clubs/clubs.module').then(m => m.ClubsModule) },
  { path: 'clubs/:club_id', loadChildren: () => import('./views/club-details/club-details.module').then(m => m.ClubDetailsModule) },
];
// @formatter:on

@NgModule({
  imports: [RouterModule.forRoot(APP_ROUTES, { useHash: false, scrollPositionRestoration: 'top' })],
  exports: [RouterModule]
})
export class RoutingModule {
}
