import { createAction, props } from "@ngrx/store";
import { ClubDetail } from "src/types";

export const LOAD_DETAILS = createAction('[CLUBS] LOAD CLUB DETAILS', props<{ clubId: number }>());
export const LOAD_DETAILS_SUCCESS = createAction('[CLUBS] LOAD CLUB DETAILS SUCCESS', props<{ club: ClubDetail }>());
export const LOAD_DETAILS_ERROR = createAction('[CLUBS] LOAD CLUB DETAILS ERROR', props<{ error: string }>());
