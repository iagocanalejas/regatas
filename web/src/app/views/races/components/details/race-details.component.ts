import { Component, OnInit } from '@angular/core';
import { Store } from "@ngrx/store";
import { State } from "src/app/reducers";
import { Gender, Participant, ParticipantCategory, Race, RaceDetail, readableCategory, readableGender } from "src/types";
import { Observable } from "rxjs";
import { selectRace } from "../../reducers";
import * as RaceActions from "../../reducers/races.actions";
import { ActivatedRoute } from "@angular/router";

// TODO: race distance
@Component({
  selector: 'app-race-details',
  templateUrl: './race-details.component.html',
  styleUrls: ['./race-details.component.scss']
})
export class RaceDetailsComponent implements OnInit {
  CATEGORIES: Array<[ParticipantCategory, Gender | null]> = [
    ['ABSOLUT', 'MALE'], ['ABSOLUT', 'FEMALE'], ['ABSOLUT', 'MIX'],
    ['VETERAN', 'MALE'], ['VETERAN', 'FEMALE'], ['VETERAN', 'MIX'],
    ['SCHOOL', null],
  ];

  race$: Observable<RaceDetail | undefined> = this._store.select(selectRace);

  series: number[] = []
  categories: Array<[ParticipantCategory, Gender | null]> = []

  constructor(private _route: ActivatedRoute, private _store: Store<State>) {
  }

  ngOnInit(): void {
    const raceId = this._route.snapshot.paramMap.get('race_id')
    if (raceId) this._store.dispatch(RaceActions.LOAD_DETAILS({ raceId: +raceId }))

    this.race$.subscribe((race) => {
        if (!race) return;

        if (this.isTimeTrial(race)) {
          this.categories = this.CATEGORIES.filter(([c, g]) => race.participants.some(p => p.category === c && (!g || p.gender === g)));
        } else {
          // pre-compute series
          const max = Math.max(...race.participants.map(x => x.series));
          this.series = Array.from(Array(max).keys());
        }
      }
    );
  }

  isTimeTrial(race: Race): boolean {
    return race.type === 'TIME_TRIAL'
  }

  hasPenalties(participants: Participant[]): boolean {
    return participants.some(p => p.penalties.some(pe => !pe.disqualification))
  }

  participantsBySeries(participants: Participant[], series: number): Participant[] {
    return participants.filter(x => x.series === series + 1).sort((p1, p2) => p1.lane - p2.lane);
  }

  participantsByCategory(participants: Participant[], [category, gender]: [ParticipantCategory, Gender | null]): Participant[] {
    return participants.filter(x => x.category === category && (!gender || x.gender === gender));
  }

  participantsWithPenalties(participants: Participant[]): Participant[] {
    return participants.filter(p => p.penalties.some(pe => !pe.disqualification))
  }

  readableTitle(value?: number): string {
    return value ? `Tanda ${value}` : 'Tiempos'
  }

  readableTimeTrialTitle([category, gender]: [ParticipantCategory, Gender | null]): string {
    return gender ? `${readableCategory(category)} ${readableGender(gender)}` : `${readableCategory(category)}`
  }
}
