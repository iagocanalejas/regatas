import { Routes } from "@angular/router";
import { ClubsComponent } from "./components/clubs.component";
import { ClubDetailsComponent } from "./components/details/club-details.component";

export const routes: Routes = [
  { path: '', component: ClubsComponent },
  { path: ':club_id', component: ClubDetailsComponent },
];
