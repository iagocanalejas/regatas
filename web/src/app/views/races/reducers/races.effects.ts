import { Injectable } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { RacesService } from "../races.service";
import * as RaceActions from "./races.actions";
import { catchError, combineLatest, exhaustMap, map, of } from "rxjs";

@Injectable()
export class RacesEffects {
  constructor(
    private _actions$: Actions,
    private _service$: RacesService,
  ) {
  }

  races$ = createEffect(() =>
    this._actions$.pipe(
      ofType(RaceActions.LOAD_RACES),
      exhaustMap(action =>
        this._service$.getRaces(action.filters, action.page).pipe(
          map(races => RaceActions.LOAD_RACES_SUCCESS({ races })),
          catchError(error => of(RaceActions.LOAD_RACES_ERROR({ error })))
        )
      )
    )
  );

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
              winner: participants[0],
              participants: participants
            }
          })),
          catchError(error => of(RaceActions.LOAD_DETAILS_ERROR({ error }))),
        )
      )
    )
  );
}
