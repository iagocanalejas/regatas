import { ActionReducer, createReducer, on } from "@ngrx/store";
import { RaceDetail } from "src/types";
import * as RaceActions from "./race-details.actions";

export const featureKey = 'race-details';

export interface State {
  // details
  race?: RaceDetail;
}

const initialState: State = {
  race: undefined,
}

export const reducer: ActionReducer<State> = createReducer(
  initialState,
  on(RaceActions.LOAD_DETAILS_SUCCESS, (state, props) => ({ ...state, race: props.race })),
);

export const selectRace = (state: State) => state.race;
