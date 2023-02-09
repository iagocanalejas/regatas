import { ActionReducerMap, createFeatureSelector, createSelector } from '@ngrx/store';
import { InjectionToken } from "@angular/core";
import * as races from "./races.reducers";
import * as root from 'src/app/reducers';

export const racesFeatureKey = 'races';

export interface RacesState {
  [races.featureKey]: races.State;
}

export interface State extends root.State {
  [racesFeatureKey]: RacesState;
}

export const FEATURE_REDUCER_TOKEN = new InjectionToken<ActionReducerMap<RacesState>>(racesFeatureKey, {
  factory: () => ({
    [races.featureKey]: races.reducer
  })
});

export const selectRacesFeatureState = createFeatureSelector<RacesState>(racesFeatureKey);
export const selectRacesState = createSelector(selectRacesFeatureState, state => state[races.featureKey]);
export const selectRaces = createSelector(selectRacesState, races.selectRaces);

export { races }
