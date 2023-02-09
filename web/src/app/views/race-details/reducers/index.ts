import { ActionReducerMap, createFeatureSelector, createSelector } from '@ngrx/store';
import { InjectionToken } from "@angular/core";
import * as races from "./race-details.reducers";
import * as root from 'src/app/reducers';

export const raceDetailsFeatureKey = 'race-details';

export interface RaceDetailsState {
  [races.featureKey]: races.State;
}

export interface State extends root.State {
  [raceDetailsFeatureKey]: RaceDetailsState;
}

export const FEATURE_REDUCER_TOKEN = new InjectionToken<ActionReducerMap<RaceDetailsState>>(raceDetailsFeatureKey, {
  factory: () => ({
    [races.featureKey]: races.reducer
  })
});

export const selectRacesFeatureState = createFeatureSelector<RaceDetailsState>(raceDetailsFeatureKey);
export const selectRacesState = createSelector(selectRacesFeatureState, state => state[races.featureKey]);
export const selectRace = createSelector(selectRacesState, races.selectRace);

export { races }
