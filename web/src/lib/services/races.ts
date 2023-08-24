import { ParticipantTransformer } from '$lib/transformers/participant.transformer';
import type { Page, PaginationResult, Race, RaceFilter } from '$lib/types';

const API_URL = 'http://localhost:8080/api';

export class RacesService {
	static #buildQueryParams(filters: RaceFilter, currentPage: number): string {
		let query = `races?page=${currentPage}`;

		if (filters.keywords) {
			query += `&keywords=${filters.keywords}`;
		}

		if (filters.year) {
			query += `&year=${filters.year}`;
		}

		if (filters.league) {
			query += `&league=${filters.league}`;
		}

		if (filters.trophy) {
			query += `&trophy=${filters.trophy}`;
		}

		if (filters.flag) {
			query += `&flag=${filters.flag}`;
		}

		return query;
	}

	static async load(filters: RaceFilter, page: PaginationResult): Promise<Page<Race> | undefined> {
		const isLastPage = page.total_pages > 0 && page.current_page == page.total_pages;
		if (isLastPage) {
			return undefined;
		}

		const response = await fetch(`${API_URL}/${this.#buildQueryParams(filters, page.current_page)}`);
		const result = (await response.json()) as Page<Race>;

		return result;
	}

	static async get(raceId: string): Promise<Race> {
		const response = await fetch(`${API_URL}/races/${raceId}`);
		const result = (await response.json()) as Race;

		result.participants = ParticipantTransformer.transformParticipants(result.participants || []);

		console.log(result);

		return result;
	}
}
