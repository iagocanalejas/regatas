import { ActionReducerMap, createFeatureSelector, createSelector } from '@ngrx/store';
import { InjectionToken } from "@angular/core";
import * as clubs from "./clubs.reducers";
import * as root from 'src/app/reducers';

export const clubsFeatureKey = 'clubs';

export interface ClubsState {
  [clubs.featureKey]: clubs.State;
}

export interface State extends root.State {
  [clubsFeatureKey]: ClubsState;
}

export const FEATURE_REDUCER_TOKEN = new InjectionToken<ActionReducerMap<ClubsState>>(clubsFeatureKey, {
  factory: () => ({
    [clubs.featureKey]: clubs.reducer
  })
});

export const selectClubsFeatureState = createFeatureSelector<ClubsState>(clubsFeatureKey);
export const selectClubsState = createSelector(selectClubsFeatureState, state => state[clubs.featureKey]);
export const selectClubs = createSelector(selectClubsState, clubs.selectClubs);
export const selectClub = createSelector(selectClubsState, clubs.selectClub);

export { clubs }
