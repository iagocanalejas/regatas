import { Injectable } from "@angular/core";
import { HttpClient } from "@angular/common/http";
import { ClubDetail, Participation } from "src/types";
import { map, Observable } from "rxjs";
import { environment } from "src/environments/environment";
import { URLBuilder } from "src/app/shared/url.builder";
import { ParticipantTransformer } from "../../shared/transformers/participant.transformer";

@Injectable({
  providedIn: 'root'
})
export class ClubDetailsService {
  constructor(private _http: HttpClient) {
  }

  getClub(clubId: number): Observable<ClubDetail> {
    const url = new URLBuilder(environment.API_PATH)
      .path('clubs/:club_id/')
      .setParam('club_id', `${clubId}`);

    return this._http.get<ClubDetail>(url.build());
  }

  getClubParticipation(clubId: number): Observable<Participation[]> {
    const url = new URLBuilder(environment.API_PATH)
      .path('clubs/:club_id/races/')
      .setParam('club_id', `${clubId}`);

    return this._http.get<Participation[]>(url.build()).pipe(
      map(participation => participation.map(p => ParticipantTransformer.transformParticipation(p)))
    );
  }
}
