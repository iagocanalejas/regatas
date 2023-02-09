import { ActionReducer, createReducer, on } from "@ngrx/store";
import * as ClubActions from "./club-details.actions";
import { ClubDetail } from "src/types";

export const featureKey = 'club-details';

export interface State {
  club?: ClubDetail;
}

const initialState: State = {
  club: undefined,
}

export const reducer: ActionReducer<State> = createReducer(
  initialState,
  on(ClubActions.LOAD_DETAILS_SUCCESS, (state, props) => ({ ...state, club: props.club })),
);

export const selectClub = (state: State) => state.club;
