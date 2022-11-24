import { RouterModule, Routes } from "@angular/router";
import { NgModule } from "@angular/core";

// @formatter:off
const APP_ROUTES: Routes = [
  { path: '', redirectTo: 'races', pathMatch: 'full' },
  { path: 'races', loadChildren: () => import('./views/races/races.module').then(m => m.RacesModule) },
  { path: 'clubs', loadChildren: () => import('./views/clubs/clubs.module').then(m => m.ClubsModule) },
  { path: 'requests', loadChildren: () => import('./views/requests/requests.module').then(m => m.RequestsModule) },
];
// @formatter:on

@NgModule({
  imports: [RouterModule.forRoot(APP_ROUTES, { useHash: false, scrollPositionRestoration: 'top' })],
  exports: [RouterModule]
})
export class RoutingModule {
}
