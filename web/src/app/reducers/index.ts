import { ActionReducerMap, createFeatureSelector, createSelector, MetaReducer } from '@ngrx/store';
import { environment } from "src/environments/environment";
import * as app from "./app.reducers";
import * as router from '@ngrx/router-store';

export interface State {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  router: router.RouterReducerState<any>;
  [app.featureKey]: app.State;
}

export const reducers: ActionReducerMap<State> = {
  [app.featureKey]: app.reducer,
  router: router.routerReducer,
};

export const metaReducers: MetaReducer<State>[] = !environment.production ? [] : [];

export const selectAppState = createFeatureSelector<app.State>(app.featureKey);
export const isLoaded = createSelector(selectAppState, app.isLoaded);
export const selectLeagues = createSelector(selectAppState, app.selectLeagues);
export const selectTrophies = createSelector(selectAppState, app.selectTrophies);
export const selectFlags = createSelector(selectAppState, app.selectFlags);
export const selectClubs = createSelector(selectAppState, app.selectClubs);
export const {selectRouteData} = router.getRouterSelectors();

export { app, router }
