import { DEFAULT_PAGE_RESULT, type Race, type RaceFilter } from '$lib/types';
import { writable, type Writable } from 'svelte/store';

export const races: Writable<Race[]> = writable([]);
export const racesPage = writable(DEFAULT_PAGE_RESULT);
export const raceFilters: Writable<RaceFilter> = writable({});

export function resetRacesStore() {
	races.set([]);
	racesPage.set(DEFAULT_PAGE_RESULT);
	raceFilters.set({});
}
