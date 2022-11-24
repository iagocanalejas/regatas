import * as AppActions from "./app.actions";
import { Injectable } from "@angular/core";
import { Actions, createEffect, ofType } from "@ngrx/effects";
import { AppService } from "../app.service";
import { catchError, combineLatest, exhaustMap, of, switchMap } from "rxjs";


@Injectable()
export class AppEffects {
  constructor(
    private _actions$: Actions,
    private _service: AppService
  ) {
  }

  data$ = createEffect(() =>
    this._actions$.pipe(
      ofType(AppActions.LOAD_DATA),
      exhaustMap(() =>
        combineLatest([
          this._service.getLeagues(),
          this._service.getTrophies(),
          this._service.getFlags(),
          this._service.getClubs(),
        ]).pipe(
          switchMap(([leagues, trophies, flags, clubs]) => [
            AppActions.LOADED_LEAGUES({ leagues }),
            AppActions.LOADED_TROPHIES({ trophies }),
            AppActions.LOADED_FLAGS({ flags }),
            AppActions.LOADED_CLUBS({ clubs }),
            AppActions.LOAD_SUCCESS(),
          ]),
          catchError((error) => of(AppActions.LOAD_ERROR({ error: error }))),
        )
      ),
    )
  );

}
