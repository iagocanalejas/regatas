import { createAction, props } from "@ngrx/store";
import { RaceDetail } from "src/types";

export const LOAD_DETAILS = createAction('[RACES] LOAD RACE DETAILS', props<{ raceId: number }>());
export const LOAD_DETAILS_SUCCESS = createAction('[RACES] LOAD RACE DETAILS SUCCESS', props<{ race: RaceDetail }>());
export const LOAD_DETAILS_ERROR = createAction('[RACES] LOAD RACE DETAILS ERROR', props<{ error: string }>());
