import { Injectable } from '@angular/core';
import { HttpClient } from "@angular/common/http";
import { Observable } from "rxjs";
import { environment } from "src/environments/environment";
import { Club, Flag, League, Organizers, Trophy } from "src/types";
import { URLBuilder } from "src/app/shared/url.builder";

@Injectable({
  providedIn: 'root'
})
export class AppService {
  constructor(private _http: HttpClient) {
  }

  getLeagues(): Observable<League[]> {
    const url = new URLBuilder(environment.API_PATH)
      .path('leagues/');
    return this._http.get<League[]>(url.build());
  }

  getTrophies(): Observable<Trophy[]> {
    const url = new URLBuilder(environment.API_PATH)
      .path('trophies/');
    return this._http.get<Trophy[]>(url.build());
  }

  getFlags(): Observable<Flag[]> {
    const url = new URLBuilder(environment.API_PATH)
      .path('flags/');
    return this._http.get<Flag[]>(url.build());
  }

  getClubs(): Observable<Club[]> {
    const url = new URLBuilder(environment.API_PATH)
      .path('clubs/');
    return this._http.get<Club[]>(url.build());
  }

  getOrganizers(): Observable<Organizers> {
    const url = new URLBuilder(environment.API_PATH)
      .path('organizers/');
    return this._http.get<Organizers>(url.build());
  }
}
