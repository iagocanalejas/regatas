import { Component, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { BehaviorSubject, combineLatest, debounceTime, distinct, filter, map, Observable, takeWhile, tap } from "rxjs";
import { DEFAULT_PAGE, Flag, Page, PaginationConfig, Race, RaceFilter, Trophy } from 'src/types';
import { selectFlags, selectTrophies, State } from "src/app/reducers";
import { Store } from "@ngrx/store";
import * as RaceActions from "../reducers/races.actions";
import { selectRaces } from "../reducers";
import { ActivatedRoute, Router } from "@angular/router";
import { PaginationComponent } from "../../../shared/components/pagination/pagination.component";

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
  @ViewChild('pagination') paginationComponent?: PaginationComponent;

  public trophies$: Observable<Trophy[]> = this._store.select(selectTrophies);
  public flags$: Observable<Flag[]> = this._store.select(selectFlags);

  public races$: Observable<Page<Race>> = this._store.select(selectRaces);

  private params: BehaviorSubject<QueryParams> = new BehaviorSubject({});
  private filtering: BehaviorSubject<RaceFilter> = new BehaviorSubject({});
  private paginating: BehaviorSubject<PaginationConfig> = new BehaviorSubject({ ...DEFAULT_PAGE });

  listOffset: number = 0;

  constructor(private _route: ActivatedRoute, private _router: Router, private _store: Store<State>) {
  }

  ngOnInit() {
    this.activeComponent = true;

    this._route.queryParams.pipe(
      tap(params => !params['league_id']
        ? this._router.navigate(['races'], { queryParams: { league_id: 2 } })
        : params),
      filter(params => !!params['league_id']),
      map(params => +params['league_id']),
      takeWhile(() => this.activeComponent),
    ).subscribe(
      leagueId => this.params.next({ leagueId })
    )

    combineLatest([
      this.params,
      this.filtering,
      this.paginating
    ]).pipe(
      distinct(),
      debounceTime(200),
      takeWhile(() => this.activeComponent),
    ).subscribe(
      ([params, filters, page]) => {
        this.listOffset = (page.page - 1) * page.itemsPerPage;

        delete filters['league']
        switch (params.leagueId) {
          case -1:
            // filter races without league
            return this._store.dispatch(RaceActions.LOAD_RACES({ filters: { ...filters, league: undefined }, page }));
          case 0:
            // filter races with any league or no league
            return this._store.dispatch(RaceActions.LOAD_RACES({ filters: { ...filters }, page }));
          default:
            // filter races with given league
            return this._store.dispatch(RaceActions.LOAD_RACES({ filters: { ...filters, league: params.leagueId }, page }));
        }
      }
    );
  }

  ngOnDestroy() {
    this.activeComponent = false;
  }

  onFilterChange(filters: RaceFilter) {
    this.filtering.next(filters);
  }

  onPageChange(page: PaginationConfig) {
    this.paginating.next(page);
  }

  onRaceSelect(race: Race) {
    this._router.navigate(['races', race.id]).then();
  }
}
