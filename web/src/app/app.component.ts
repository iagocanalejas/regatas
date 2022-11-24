import { Component, OnDestroy, OnInit } from '@angular/core';
import { Store } from "@ngrx/store";
import { selectLeagues, State } from "./reducers";
import * as AppActions from "./reducers/app.actions";
import { Router } from "@angular/router";
import { Gender, League } from "src/types";
import { Observable } from "rxjs";

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit, OnDestroy {
  private activeComponent: boolean = false;

  public leagues$: Observable<League[]> = this._store.select(selectLeagues);

  navbarOpen: boolean = false

  constructor(private _router: Router, private _store: Store<State>) {
  }

  get route() {
    return this._router.url;
  }

  get showRequestButton() {
    // Only show the navbar request button for root pages
    return this.route.slice(1).split('/').length === 1 && false // TODO
  }

  getCurrentLeagueName(leagues: League[]): string {
    const league = this._router.url.split('league_id=')[1]
    const leagueName = league ? leagues.find(l => l.id === +league)?.name : 'Regatas'
    return leagueName ? leagueName : 'Regatas'
  }

  getLeagues(leagues: League[], gender: Gender): League[] {
    return leagues.filter(l => l.gender === gender)
  }

  ngOnInit(): void {
    this.activeComponent = true;
    this._store.dispatch(AppActions.LOAD_DATA());
  }

  ngOnDestroy(): void {
    this.activeComponent = false;
  }

  onNavbarLinkSelected(link: string, params?: { [key: string]: number }) {
    this._router.navigate([link], { ...(params ? { queryParams: params } : {}) }).then();
  }

  onAddSelected() {
    const type = this.route.includes('clubs') ? 'club' : 'race';
    this._router.navigate(['/requests'], { queryParams: { type } }).then();
  }
}
