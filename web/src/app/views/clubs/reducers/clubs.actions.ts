import { createAction, props } from "@ngrx/store";
import { Club } from "src/types";

export const LOAD_CLUBS = createAction('[CLUBS] LOAD CLUBS');
export const LOAD_CLUBS_SUCCESS = createAction('[CLUBS] LOAD CLUBS SUCCESS', props<{ clubs: Club[] }>());
export const LOAD_CLUBS_ERROR = createAction('[CLUBS] LOAD CLUBS ERROR', props<{ error: string }>());
