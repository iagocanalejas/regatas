import { Component, OnInit } from '@angular/core';
import { Store } from "@ngrx/store";
import { State } from "src/app/reducers";
import { Participant, Race, RaceDetail } from "src/types";
import { Observable } from "rxjs";
import { selectRace } from "../../reducers";
import * as RaceActions from "../../reducers/races.actions";
import { ActivatedRoute } from "@angular/router";

@Component({
  selector: 'app-race-details',
  templateUrl: './race-details.component.html',
  styleUrls: ['./race-details.component.scss']
})
export class RaceDetailsComponent implements OnInit {

  race$: Observable<RaceDetail | undefined> = this._store.select(selectRace);

  constructor(private _route: ActivatedRoute, private _store: Store<State>) {
  }

  ngOnInit(): void {
    const raceId = this._route.snapshot.paramMap.get('race_id')
    if (raceId) {
      this._store.dispatch(RaceActions.LOAD_DETAILS({ raceId: +raceId }))
    }
  }

  isTimeTrial(race: Race): boolean {
    return race.type === 'TIME_TRIAL'
  }

  seriesList(participants: Participant[]): number[] {
    const max = Math.max(...participants.map(x => x.series));
    return Array.from(Array(max).keys());
  }

  getParticipants(participants: Participant[], series: number): Participant[] {
    return participants.filter(x => x.series === series + 1).sort((p1, p2) => p1.lane - p2.lane);
  }

  getParticipantsWithPenalties(participants: Participant[]): Participant[] {
    return participants.filter(p => p.penalties && p.penalties.some(pe => !pe.disqualification))
  }

}
