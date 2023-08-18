import type { League } from '$lib/types';
import { writable, type Writable } from 'svelte/store';

export const leagues: Writable<League[]> = writable([]);
