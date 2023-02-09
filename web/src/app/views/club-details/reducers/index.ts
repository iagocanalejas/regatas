import { ActionReducerMap, createFeatureSelector, createSelector } from '@ngrx/store';
import { InjectionToken } from "@angular/core";
import * as clubDetails from "./club-details.reducers";
import * as root from 'src/app/reducers';

export const clubDetailsFeatureKey = 'club-details';

export interface ClubDetailsState {
  [clubDetails.featureKey]: clubDetails.State;
}

export interface State extends root.State {
  [clubDetailsFeatureKey]: ClubDetailsState;
}

export const FEATURE_REDUCER_TOKEN = new InjectionToken<ActionReducerMap<ClubDetailsState>>(clubDetailsFeatureKey, {
  factory: () => ({
    [clubDetails.featureKey]: clubDetails.reducer
  })
});

export const selectClubsFeatureState = createFeatureSelector<ClubDetailsState>(clubDetailsFeatureKey);
export const selectClubsState = createSelector(selectClubsFeatureState, state => state[clubDetails.featureKey]);
export const selectClub = createSelector(selectClubsState, clubDetails.selectClub);

export { clubDetails }
