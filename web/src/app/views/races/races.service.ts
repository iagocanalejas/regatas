import { Injectable } from '@angular/core';
import { HttpClient } from "@angular/common/http";
import { map, Observable, of, switchMap } from "rxjs";
import { Page, PaginationConfig, Race, RaceFilter } from "src/types";
import { URLBuilder } from "src/app/shared/url.builder";
import { environment } from "src/environments/environment";
import { RaceTransformer } from "../../shared/transformers/race.transformer";

@Injectable({
  providedIn: 'root'
})
export class RacesService {
  constructor(private _http: HttpClient) {
  }

  getRaces(filters: RaceFilter, page: PaginationConfig): Observable<Page<Race>> {
    const url = new URLBuilder(environment.API_PATH)
      .path('races/')
      .setFilters(filters)
      .setPage(page);

    return this._http.get<Page<Race>>(url.build()).pipe(
      map(page => ({ ...page, results: page.results.map(race => RaceTransformer.transformRace(race)) })),
      switchMap(responsePage => (responsePage.count === 0 && filters.year === new Date().getFullYear())
        ? this.getRaces({ ...filters, year: new Date().getFullYear() - 1 }, page)
        : of(responsePage)
      )
    );
  }
}
