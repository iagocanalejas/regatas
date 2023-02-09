import { Injectable } from '@angular/core';
import { HttpClient } from "@angular/common/http";
import { map, Observable } from "rxjs";
import { Participant, RaceDetail } from "src/types";
import { URLBuilder } from "src/app/shared/url.builder";
import { environment } from "src/environments/environment";
import { RaceTransformer } from "../../shared/transformers/race.transformer";
import { ParticipantTransformer } from "../../shared/transformers/participant.transformer";

@Injectable({
  providedIn: 'root'
})
export class RaceDetailsService {
  constructor(private _http: HttpClient) {
  }

  getRace(raceId: number): Observable<RaceDetail> {
    const url = new URLBuilder(environment.API_PATH)
      .path('races/:race_id/')
      .setParam('race_id', raceId.toString());

    return this._http.get<RaceDetail>(url.build()).pipe(
      map(race => RaceTransformer.transformRaceDetails(race))
    );
  }

  getRaceParticipants(raceId: number): Observable<Participant[]> {
    const url = new URLBuilder(environment.API_PATH)
      .path('races/:race_id/participants/')
      .setParam('race_id', raceId.toString());

    return this._http.get<Participant[]>(url.build()).pipe(
      map(participants => ParticipantTransformer.transformParticipants(participants)),
    );
  }
}
