import type { League } from '$lib/types';

export class LeaguesService {
	static async load(): Promise<League[] | undefined> {
		const response = await fetch('http://localhost:8080/api/leagues');
		const result = (await response.json()) as League[];

		return result;
	}
}
