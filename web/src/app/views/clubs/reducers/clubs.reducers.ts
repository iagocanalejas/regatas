import { ActionReducer, createReducer, on } from "@ngrx/store";
import * as ClubActions from "./clubs.actions";
import { Club, ClubDetail } from "src/types";

export const featureKey = 'clubs';

export interface State {
  // list
  clubs: Club[];
  // details
  club?: ClubDetail;
}

const initialState: State = {
  clubs: [],
  club: undefined,
}

export const reducer: ActionReducer<State> = createReducer(
  initialState,
  on(ClubActions.LOAD_CLUBS_SUCCESS, (state, props) => ({ ...state, clubs: props.clubs })),
  on(ClubActions.LOAD_DETAILS_SUCCESS, (state, props) => ({ ...state, club: props.club })),
);

export const selectClubs = (state: State) => state.clubs;
export const selectClub = (state: State) => state.club;
