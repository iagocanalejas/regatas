import type { Page, PaginationResult, Race, RaceFilter } from '$lib/types';

export class RacesService {
	static #buildQueryParams(filters: RaceFilter, currentPage: number): string {
		let query = `/api/races?page=${currentPage}`;

		if (!!filters.keywords) {
			query += `&keywords=${filters.keywords}`;
		}

		if (!!filters.year) {
			query += `&year=${filters.year}`;
		}

		if (!!filters.league) {
			query += `&league=${filters.league}`;
		}

		return query;
	}

	static async load(filters: RaceFilter, page: PaginationResult): Promise<Page<Race> | undefined> {
		let isLastPage = page.total_pages > 0 && page.current_page == page.total_pages;
		if (isLastPage) {
			return undefined;
		}

		const response = await fetch(`http://localhost:8080${this.#buildQueryParams(filters, page.current_page)}`);
		const result = (await response.json()) as Page<Race>;

		return result;
	}
}
