import { ActionReducer, createReducer, on } from "@ngrx/store";
import * as ClubActions from "./clubs.actions";
import { Club } from "src/types";

export const featureKey = 'clubs';

export interface State {
  clubs: Club[];
}

const initialState: State = {
  clubs: [],
}

export const reducer: ActionReducer<State> = createReducer(
  initialState,
  on(ClubActions.LOAD_CLUBS_SUCCESS, (state, props) => ({ ...state, clubs: props.clubs })),
);

export const selectClubs = (state: State) => state.clubs;
