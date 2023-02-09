import { Injectable } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import * as RaceActions from "./race-details.actions";
import { catchError, combineLatest, exhaustMap, map, of } from "rxjs";
import { RaceDetailsService } from "../race-details.service";

@Injectable()
export class RaceDetailsEffects {
  constructor(
    private _actions$: Actions,
    private _service$: RaceDetailsService,
  ) {
  }

  race$ = createEffect(() =>
    this._actions$.pipe(
      ofType(RaceActions.LOAD_DETAILS),
      exhaustMap(action =>
        combineLatest([
          this._service$.getRace(action.raceId),
          this._service$.getRaceParticipants(action.raceId),
        ]).pipe(
          map(([race, participants]) => RaceActions.LOAD_DETAILS_SUCCESS({
            race: {
              ...race,
              participants: participants
            }
          })),
          catchError(error => of(RaceActions.LOAD_DETAILS_ERROR({ error }))),
        )
      )
    )
  );
}
