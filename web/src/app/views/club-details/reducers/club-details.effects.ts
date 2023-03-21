import { Injectable } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import * as ClubActions from "./club-details.actions";
import { catchError, combineLatest, exhaustMap, map, of } from "rxjs";
import { ClubDetailsService } from "../club-details.service";

@Injectable()
export class ClubDetailsEffects {
  constructor(
    private _actions$: Actions,
    private _service$: ClubDetailsService
  ) {
  }

  club$ = createEffect(() =>
    this._actions$.pipe(
      ofType(ClubActions.LOAD_DETAILS),
      exhaustMap(action =>
        combineLatest([
          this._service$.getClub(action.clubId),
          this._service$.getClubParticipation(action.clubId, action.filters, action.page),
        ]).pipe(
          map(([club, participation]) => ClubActions.LOAD_DETAILS_SUCCESS({
            club: {
              ...club,
              participation: participation
            }
          })),
          catchError(error => of(ClubActions.LOAD_DETAILS_ERROR({ error }))),
        )
      )
    )
  );
}
