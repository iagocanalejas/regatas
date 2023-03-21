import { Component, OnInit } from '@angular/core';
import { Store } from "@ngrx/store";
import { State } from "src/app/reducers";
import { categoryGender_es, Gender, Participant, ParticipantCategory, ParticipantUtils, Race, RaceDetail } from "src/types";
import { Observable } from "rxjs";
import { selectRace } from "../reducers";
import * as RaceDetailsActions from "../reducers/race-details.actions";
import { ActivatedRoute } from "@angular/router";

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

  ngOnInit() {
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

    const raceId = this._route.snapshot.paramMap.get('race_id')
    if (raceId) this._store.dispatch(RaceDetailsActions.LOAD_DETAILS({ raceId: +raceId }))
  }

  isTimeTrial(race: Race): boolean {
    return race.type === 'TIME_TRIAL'
  }

  hasPenalties(participants: Participant[]): boolean {
    return participants.some(p => p.penalties.some(pe => !pe.disqualification))
  }

  winner(race: RaceDetail): Participant | undefined {
    if (!this.isTimeTrial(race))
      return this.participants(race.participants)[0];
    return undefined;
  }

  participants(participants: Participant[]): Participant[] {
    return [...participants].sort((p1, p2) => ParticipantUtils.compareTimes(p1, p2));
  }

  participantsBySeries(participants: Participant[], series: number): Participant[] {
    return participants.filter(x => x.series === series + 1)
      .sort((p1, p2) => p1.lane - p2.lane);
  }

  participantsByCategory(participants: Participant[], [category, gender]: [ParticipantCategory, Gender | null]): Participant[] {
    return participants.filter(x => x.category === category && (!gender || x.gender === gender))
      .sort((p1, p2) => ParticipantUtils.compareTimes(p1, p2));
  }

  participantsWithPenalties(participants: Participant[]): Participant[] {
    return participants.filter(p => p.penalties.some(pe => !pe.disqualification))
  }

  distance(participants: Participant[]): number {
    const valid_distances = participants.filter(p => p.distance).map(p => p.distance);
    return valid_distances.reduce((p, c) => p + c, 0) / valid_distances.length;
  }

  readableTitle(value?: number): string {
    return value ? `Tanda ${value}` : 'Tiempos'
  }

  readableCategoryGender = categoryGender_es;
}
