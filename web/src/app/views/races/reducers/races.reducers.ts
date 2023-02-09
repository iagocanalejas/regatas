import { ActionReducer, createReducer, on } from "@ngrx/store";
import { DEFAULT_PAGE_RESULT, Page, Race } from "src/types";
import * as RaceActions from "./races.actions";

export const featureKey = 'races';

export interface State {
  // list
  races: Page<Race>;
}

const initialState: State = {
  races: DEFAULT_PAGE_RESULT<Race>(),
}

export const reducer: ActionReducer<State> = createReducer(
  initialState,
  on(RaceActions.LOAD_RACES_SUCCESS, (state, props) => ({ ...state, races: props.races })),
);

export const selectRaces = (state: State) => state.races;
