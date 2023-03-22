import type { Flag, League, Trophy } from '$lib/types';
import { writable, type Writable } from 'svelte/store';

export const leagues: Writable<League[]> = writable([]);
export const trophies: Writable<Trophy[]> = writable([]);
export const flags: Writable<Flag[]> = writable([]);
