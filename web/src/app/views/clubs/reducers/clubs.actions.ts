import { createAction, props } from "@ngrx/store";
import { Club, ClubDetail, PaginationConfig } from "src/types";

export const LOAD_CLUBS = createAction('[CLUBS] LOAD CLUBS');
export const LOAD_CLUBS_SUCCESS = createAction('[CLUBS] LOAD CLUBS SUCCESS', props<{ clubs: Club[] }>());
export const LOAD_CLUBS_ERROR = createAction('[CLUBS] LOAD CLUBS ERROR', props<{ error: string }>());

export const LOAD_DETAILS = createAction('[CLUBS] LOAD CLUB DETAILS', props<{ clubId: number, page: PaginationConfig }>());
export const LOAD_DETAILS_SUCCESS = createAction('[CLUBS] LOAD CLUB DETAILS SUCCESS', props<{ club: ClubDetail }>());
export const LOAD_DETAILS_ERROR = createAction('[CLUBS] LOAD CLUB DETAILS ERROR', props<{ error: string }>());
