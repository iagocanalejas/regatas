import { ActionReducer, createReducer, on } from "@ngrx/store";
import { DEFAULT_PAGE_RESULT, Page, Race, RaceDetail } from "src/types";
import * as RaceActions from "./races.actions";

export const featureKey = 'races';

export interface State {
  // list
  races: Page<Race>;
  // details
  race?: RaceDetail;
}

const initialState: State = {
  races: DEFAULT_PAGE_RESULT<Race>(),
  race: undefined,
}

export const reducer: ActionReducer<State> = createReducer(
  initialState,
  on(RaceActions.LOAD_RACES_SUCCESS, (state, props) => ({ ...state, races: props.races })),
  on(RaceActions.LOAD_DETAILS_SUCCESS, (state, props) => ({ ...state, race: props.race })),
);

export const selectRaces = (state: State) => state.races;
export const selectRace = (state: State) => state.race;
