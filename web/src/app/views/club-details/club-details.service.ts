import { Injectable } from "@angular/core";
import { HttpClient } from "@angular/common/http";
import { ClubDetail, Page, PaginationConfig, Race } from "src/types";
import { map, Observable } from "rxjs";
import { environment } from "src/environments/environment";
import { RaceTransformer } from "../../shared/transformers/race.transformer";
import { URLBuilder } from "src/app/shared/url.builder";

@Injectable({
  providedIn: 'root'
})
export class ClubDetailsService {
  constructor(private _http: HttpClient) {
  }

  getClub(clubId: number): Observable<ClubDetail> {
    const url = new URLBuilder(environment.API_PATH)
      .path('clubs/')
      .setParam('club_id', clubId.toString());

    return this._http.get<ClubDetail>(url.build());
  }

  getClubRaces(clubId: number, page: PaginationConfig): Observable<Page<Race>> {
    const url = new URLBuilder(environment.API_PATH)
      .path('races/')
      .addQueryParam('limit', page.itemsPerPage.toString())
      .addQueryParam('offset', ((page.page - 1) * page.itemsPerPage).toString())
      .addQueryParam('participant_club', clubId.toString());

    return this._http.get<Page<Race>>(url.build()).pipe(
      map(page => ({ ...page, results: page.results.map(race => RaceTransformer.transformRace(race)) }))
    );
  }
}
