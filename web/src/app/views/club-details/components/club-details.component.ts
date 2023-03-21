import { Component, OnDestroy, OnInit } from "@angular/core";
import { BehaviorSubject, combineLatest, debounceTime, Observable, ReplaySubject, takeWhile } from "rxjs";
import { ActivatedRoute, Router } from "@angular/router";
import { Store } from "@ngrx/store";
import { selectFlags, selectTrophies, State } from "src/app/reducers";
import * as ClubDetailsActions from "../reducers/club-details.actions";
import { ClubDetail, DEFAULT_PAGE, Flag, PaginationConfig, ParticipantFilter, Race, Trophy } from "src/types";
import { selectClub } from "../reducers";

interface QueryParams {
  clubId: number;
}

@Component({
  selector: 'club-details',
  templateUrl: './club-details.component.html',
  styleUrls: ['./club-details.component.scss'],
})
export class ClubDetailsComponent implements OnInit, OnDestroy {
  private activeComponent: boolean = false;

  public trophies$: Observable<Trophy[]> = this._store.select(selectTrophies);
  public flags$: Observable<Flag[]> = this._store.select(selectFlags);

  club$: Observable<ClubDetail | undefined> = this._store.select(selectClub);

  private params = new ReplaySubject<QueryParams>();
  private filtering = new BehaviorSubject<ParticipantFilter>({});
  private sorting = new BehaviorSubject<string>('date');
  private paginating = new BehaviorSubject<PaginationConfig>({ ...DEFAULT_PAGE, itemsPerPage: 250 });

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
      debounceTime(200),
      takeWhile(() => this.activeComponent),
    ).subscribe(
      ([params, filters, sortBy, page]) => {
        this.listOffset = (page.page - 1) * page.itemsPerPage;
        return this._store.dispatch(ClubDetailsActions.LOAD_DETAILS({ clubId: params.clubId, page: { ...page, sortBy }, filters }));
      }
    );

    const clubId = this._route.snapshot.paramMap.get('club_id')
    if (clubId) this.params.next({ clubId: +clubId })
  }

  ngOnDestroy() {
    this.activeComponent = false;
  }

  changeFilters(filters: ParticipantFilter) {
    this.filtering.next(filters);
  }

  changeSorting(sortBy: string) {
    this.sorting.next(sortBy);
  }

  changePage(page: PaginationConfig) {
    this.paginating.next(page);
  }

  selectRace(race: Race) {
    this._router.navigate(['races', race.id]).then();
  }
}
