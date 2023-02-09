import { Injectable } from "@angular/core";
import { HttpClient } from "@angular/common/http";
import { Club } from "src/types";
import { Observable } from "rxjs";
import { environment } from "src/environments/environment";
import { URLBuilder } from "src/app/shared/url.builder";

@Injectable({
  providedIn: 'root'
})
export class ClubsService {
  constructor(private _http: HttpClient) {
  }

  getClubs(): Observable<Club[]> {
    const url = new URLBuilder(environment.API_PATH)
      .path('clubs/');

    return this._http.get<Club[]>(url.build());
  }
}
