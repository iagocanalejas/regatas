import { Injectable } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { ClubsService } from "../clubs.service";
import * as ClubActions from "../reducers/clubs.actions";
import { catchError, combineLatest, exhaustMap, map, of } from "rxjs";

@Injectable()
export class ClubsEffects {
  constructor(
    private _actions$: Actions,
    private _service$: ClubsService
  ) {
  }

  clubs$ = createEffect(() =>
    this._actions$.pipe(
      ofType(ClubActions.LOAD_CLUBS),
      exhaustMap(() =>
        this._service$.getClubs().pipe(
          map(clubs => ClubActions.LOAD_CLUBS_SUCCESS({ clubs })),
          catchError(error => of(ClubActions.LOAD_CLUBS_ERROR({ error })))
        )
      )
    )
  );

  club$ = createEffect(() =>
    this._actions$.pipe(
      ofType(ClubActions.LOAD_DETAILS),
      exhaustMap(action =>
        combineLatest([
          this._service$.getClub(action.clubId),
          this._service$.getClubRaces(action.clubId, action.page),
        ]).pipe(
          map(([club, races]) => ClubActions.LOAD_DETAILS_SUCCESS({
            club: {
              ...club,
              races: races
            }
          })),
          catchError(error => of(ClubActions.LOAD_DETAILS_ERROR({ error }))),
        )
      )
    )
  );
}
