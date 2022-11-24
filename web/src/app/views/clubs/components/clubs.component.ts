import { Component, OnDestroy, OnInit } from "@angular/core";
import { Router } from "@angular/router";
import { Store } from "@ngrx/store";
import { selectClubs, State } from "src/app/reducers";
import * as ClubActions from "../reducers/clubs.actions";
import { Observable } from "rxjs";
import { Club } from "src/types";

@Component({
  selector: 'clubs',
  templateUrl: './clubs.component.html',
  styleUrls: ['./clubs.component.scss']
})
export class ClubsComponent implements OnInit, OnDestroy {
  private activeComponent: boolean = false;

  public clubs$: Observable<Club[]> = this._store.select(selectClubs);

  keywords: string = '';

  get windowsWidth() {
    return window.innerWidth
  }

  constructor(private _router: Router, private _store: Store<State>) {
  }

  ngOnInit() {
    this.activeComponent = true;
    this._store.dispatch(ClubActions.LOAD_CLUBS());
  }

  ngOnDestroy() {
    this.activeComponent = false;
  }

  getFilteredClubs(clubs: Club[]): Club[] {
    return clubs.filter(c => c.name.toLowerCase().includes(this.keywords.toLowerCase()));
  }

  onClubSelect(club: Club) {
    this._router.navigate(['clubs', club.id]).then();
  }

  clearKeywords() {
    this.keywords = '';
  }
}
