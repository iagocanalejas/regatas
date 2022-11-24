import { ActionReducer, createReducer, on } from "@ngrx/store";
import { Club, Flag, League, Trophy } from "src/types";
import * as AppActions from "./app.actions";

export const featureKey = 'app';

export interface State {
  leagues: League[];
  trophies: Trophy[];
  flags: Flag[];
  clubs: Club[];
  loaded: boolean;
}

const initialState: State = {
  leagues: [],
  trophies: [],
  flags: [],
  clubs: [],
  loaded: false,
}

export const reducer: ActionReducer<State> = createReducer(
  initialState,
  on(AppActions.LOAD_SUCCESS, (state) => ({...state, loaded: true})),
  on(AppActions.LOADED_LEAGUES, (state, props) => ({...state, leagues: props.leagues})),
  on(AppActions.LOADED_TROPHIES, (state, props) => ({...state, trophies: props.trophies})),
  on(AppActions.LOADED_FLAGS, (state, props) => ({...state, flags: props.flags})),
  on(AppActions.LOADED_CLUBS, (state, props) => ({...state, clubs: props.clubs})),
);

export const isLoaded = (state: State) => state.loaded;
export const selectLeagues = (state: State) => state.leagues;
export const selectTrophies = (state: State) => state.trophies;
export const selectFlags = (state: State) => state.flags;
export const selectClubs = (state: State) => state.clubs;
