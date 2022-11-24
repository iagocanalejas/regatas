import { createAction, props } from "@ngrx/store";
import { Club, Flag, League, Trophy } from "src/types";

export const LOAD_DATA = createAction('[APP] LOAD APP DATA');
export const LOAD_SUCCESS = createAction('[APP] LOAD SUCCESS');
export const LOAD_ERROR = createAction('[APP] LOAD ERROR', props<{ error: string }>());

export const LOADED_LEAGUES = createAction('[APP] LOADED LEAGUES', props<{ leagues: League[] }>());
export const LOADED_TROPHIES = createAction('[APP] LOADED TROPHIES', props<{ trophies: Trophy[] }>());
export const LOADED_FLAGS = createAction('[APP] LOADED FLAGS', props<{ flags: Flag[] }>());
export const LOADED_CLUBS = createAction('[APP] LOADED CLUBS', props<{ clubs: Club[] }>());
