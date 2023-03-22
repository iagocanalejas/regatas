import type { Flag, League, Trophy } from '$lib/types';

const API_URL = 'http://localhost:8080/api';

export class GlobalsService {
	static async loadLeagues(): Promise<League[]> {
		const response = await fetch(`${API_URL}/leagues`);
		const result = (await response.json()) as League[];

		return result || [];
	}

	static async loadTrophies(): Promise<Trophy[]> {
		const response = await fetch(`${API_URL}/trophies`);
		const result = (await response.json()) as Trophy[];

		return result || [];
	}

	static async loadFlags(): Promise<Flag[]> {
		const response = await fetch(`${API_URL}/flags`);
		const result = (await response.json()) as Flag[];

		return result || [];
	}
}
