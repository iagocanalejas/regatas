import { createAction, props } from "@ngrx/store";
import { Page, PaginationConfig, Race, RaceDetail, RaceFilter } from "src/types";

export const LOAD_RACES = createAction('[RACES] LOAD RACES', props<{ filters: RaceFilter, page: PaginationConfig }>());
export const LOAD_RACES_SUCCESS = createAction('[RACES] LOAD RACES SUCCESS', props<{ races: Page<Race> }>());
export const LOAD_RACES_ERROR = createAction('[RACES] LOAD RACES ERROR', props<{ error: string }>());

export const LOAD_DETAILS = createAction('[RACES] LOAD RACE DETAILS', props<{ raceId: number }>());
export const LOAD_DETAILS_SUCCESS = createAction('[RACES] LOAD RACE DETAILS SUCCESS', props<{ race: RaceDetail }>());
export const LOAD_DETAILS_ERROR = createAction('[RACES] LOAD RACE DETAILS ERROR', props<{ error: string }>());
