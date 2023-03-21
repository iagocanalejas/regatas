import { Component, OnDestroy, OnInit } from '@angular/core';
import { BehaviorSubject, combineLatest, debounceTime, distinct, Observable, takeWhile } from "rxjs";
import { DEFAULT_PAGE, Flag, Page, PaginationConfig, Race, RaceFilter, Trophy } from 'src/types';
import { selectFlags, selectTrophies, State } from "src/app/reducers";
import { Store } from "@ngrx/store";
import * as RaceActions from "../reducers/races.actions";
import { selectRaces } from "../reducers";
import { ActivatedRoute, Router } from "@angular/router";

interface QueryParams {
  leagueId?: number;
}

@Component({
  selector: 'races',
  templateUrl: './races.component.html',
  styleUrls: ['./races.component.scss']
})
export class RacesComponent implements OnInit, OnDestroy {
  private activeComponent: boolean = false;

  public trophies$: Observable<Trophy[]> = this._store.select(selectTrophies);
  public flags$: Observable<Flag[]> = this._store.select(selectFlags);

  public races$: Observable<Page<Race>> = this._store.select(selectRaces);

  private params: BehaviorSubject<QueryParams> = new BehaviorSubject({});
  private filtering: BehaviorSubject<RaceFilter> = new BehaviorSubject({});
  private sorting: BehaviorSubject<string> = new BehaviorSubject('date');
  private paginating: BehaviorSubject<PaginationConfig> = new BehaviorSubject({ ...DEFAULT_PAGE });

  listOffset: number = 0;

  constructor(private _route: ActivatedRoute, private _router: Router, private _store: Store<State>) {
  }

  ngOnInit() {
    this.activeComponent = true;

    combineLatest([
      this.params,
      this.filtering,
      this.sorting,
      this.paginating
    ]).pipe(
      distinct(),
      debounceTime(300),
      takeWhile(() => this.activeComponent),
    ).subscribe(
      ([params, filters, sortBy, page]) => {
        this.listOffset = (page.page - 1) * page.itemsPerPage;

        delete filters['league']
        switch (params.leagueId) {
          case -1:
            // filter races without league
            return this._store.dispatch(RaceActions.LOAD_RACES({
              filters: { ...filters, league: undefined },
              page: { ...page, sortBy }
            }));
          case 0:
            // filter races with any league or no league
            return this._store.dispatch(RaceActions.LOAD_RACES({
              filters: { ...filters },
              page: { ...page, sortBy }
            }));
          default:
            // filter races with given league
            return this._store.dispatch(RaceActions.LOAD_RACES({
              filters: { ...filters, league: params.leagueId },
              page: { ...page, sortBy }
            }));
        }
      }
    );

    this._route.queryParams.pipe(
      takeWhile(() => this.activeComponent),
    ).subscribe(
      params => {
        if (!params['league_id']) {
          this._router.navigate(['races'], { queryParams: { league_id: 0 } })
          return
        }
        return this.params.next({ leagueId: +params['league_id'] })
      }
    );
  }

  ngOnDestroy() {
    this.activeComponent = false;
  }

  changeFilters(filters: RaceFilter) {
    this.filtering.next(filters);
  }

  changePage(page: PaginationConfig) {
    this.paginating.next(page);
  }

  changeSorting(sortBy: string) {
    this.sorting.next(sortBy);
  }

  selectRace(race: Race) {
    this._router.navigate(['races', race.id]).then();
  }
}
