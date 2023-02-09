import { createAction, props } from "@ngrx/store";
import { Page, PaginationConfig, Race, RaceFilter } from "src/types";

export const LOAD_RACES = createAction('[RACES] LOAD RACES', props<{ filters: RaceFilter, page: PaginationConfig }>());
export const LOAD_RACES_SUCCESS = createAction('[RACES] LOAD RACES SUCCESS', props<{ races: Page<Race> }>());
export const LOAD_RACES_ERROR = createAction('[RACES] LOAD RACES ERROR', props<{ error: string }>());
