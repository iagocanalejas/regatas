import { ParticipantTransformer } from '$lib/transformers/participant.transformer';
import type { Page, PaginationConfig, Race, RaceFilter } from '$lib/types';

const API_URL = 'http://localhost:8080/api';

export class RacesService {
	static #buildQueryParams(filters: RaceFilter, page: PaginationConfig): string {
		let query = `races?page=${page.page}`;

		if (page.itemsPerPage) {
			query += `&limit=${page.itemsPerPage}`;
		}

		if (filters.keywords) {
			query += `&keywords=${filters.keywords}`;
		}

		if (filters.year) {
			query += `&year=${filters.year}`;
		}

		if (filters.league) {
			query += `&league=${filters.league}`;
		}

		if (filters.trophyOrFlag) {
			query += `&trophyOrFlag=${filters.trophyOrFlag[0]},${filters.trophyOrFlag[1]}`;
		}

		if (filters.trophy) {
			query += `&trophy=${filters.trophy}`;
		}

		if (filters.participant) {
			query += `&participant=${filters.participant}`;
		}

		if (filters.flag) {
			query += `&flag=${filters.flag}`;
		}

		return query;
	}

	static async load(filters: RaceFilter, page: PaginationConfig): Promise<Page<Race>> {
		const response = await fetch(`${API_URL}/${this.#buildQueryParams(filters, page)}`);
		const result = (await response.json()) as Page<Race>;

		return result;
	}

	static async get(raceId: string): Promise<Race> {
		const response = await fetch(`${API_URL}/races/${raceId}`);
		const result = (await response.json()) as Race;

		result.participants = ParticipantTransformer.transformParticipants(result.participants || []);

		return result;
	}

	static async getRelated(race: Race): Promise<Race[]> {
		const page: PaginationConfig = {
			page: 0,
			itemsPerPage: 10
		};

		let result: Page<Race>;
		if (race.trophy?.id && race.flag?.id) {
			result = await this.load({ trophyOrFlag: [race.trophy.id, race.flag.id] }, page);
		} else if (race.trophy?.id) {
			result = await this.load({ trophy: race.trophy.id }, page);
		} else if (race.flag?.id) {
			result = await this.load({ trophy: race.flag.id }, page);
		} else {
			throw 'Something went terrible wrong';
		}

		return result.results;
	}
}
