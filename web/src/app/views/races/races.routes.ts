import { Routes } from "@angular/router";
import { RacesComponent } from "./components/races.component";
import { RaceDetailsComponent } from "./components/details/race-details.component";

export const routes: Routes = [
  { path: '', component: RacesComponent },
  { path: ':race_id', component: RaceDetailsComponent },
];
