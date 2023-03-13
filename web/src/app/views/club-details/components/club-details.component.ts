import { Component, OnDestroy, OnInit, ViewChild } from "@angular/core";
import { BehaviorSubject, combineLatest, debounceTime, filter, Observable, takeWhile } from "rxjs";
import { ActivatedRoute, Router } from "@angular/router";
import { Store } from "@ngrx/store";
import { State } from "src/app/reducers";
import * as ClubDetailsActions from "../reducers/club-details.actions";
import { ClubDetail, DEFAULT_PAGE, PaginationConfig, Race } from "src/types";
import { selectClub } from "../reducers";
import { PaginationComponent } from "../../../shared/components/pagination/pagination.component";

interface QueryParams {
  clubId?: number;
}

@Component({
  selector: 'club-details',
  templateUrl: './club-details.component.html',
  styleUrls: ['./club-details.component.scss'],
})
export class ClubDetailsComponent implements OnInit, OnDestroy {
  private activeComponent: boolean = false;
  @ViewChild('pagination') paginationComponent?: PaginationComponent;

  club$: Observable<ClubDetail | undefined> = this._store.select(selectClub);

  private params: BehaviorSubject<QueryParams> = new BehaviorSubject({});
  private paginating: BehaviorSubject<PaginationConfig> = new BehaviorSubject({ ...DEFAULT_PAGE, itemsPerPage: 100 });

  listOffset: number = 0;

  constructor(private _route: ActivatedRoute, private _router: Router, private _store: Store<State>) {
  }

  ngOnInit(): void {
    this.activeComponent = true;

    this._route.paramMap.pipe(
      filter(params => !!params.get('club_id')),
      takeWhile(() => this.activeComponent),
    ).subscribe(
      params => this.params.next({ clubId: +params.get('club_id')! })
    )

    combineLatest([
      this.params,
      this.paginating
    ]).pipe(
      debounceTime(200),
      takeWhile(() => this.activeComponent),
    ).subscribe(
      ([params, page]) => {
        this.listOffset = (page.page - 1) * page.itemsPerPage;
        return this._store.dispatch(ClubDetailsActions.LOAD_DETAILS({ clubId: params.clubId!, page }));
      }
    );
  }

  ngOnDestroy() {
    this.activeComponent = false;
  }

  onPageChange(page: PaginationConfig) {
    this.paginating.next(page);
  }

  onRaceSelect(race: Race) {
    this._router.navigate(['races', race.id]).then();
  }
}
