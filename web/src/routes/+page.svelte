<script lang="ts">
	import { races, racesPage, raceFilters } from '$lib/stores/races';
	import { DEFAULT_PAGE_RESULT, type League, type Page, type Race } from '$lib/types';
	import { onDestroy, onMount } from 'svelte';
	import SearchRace from '$lib/components/SearchRace.svelte';
	import Pagination from '$lib/components/Pagination.svelte';

	onMount(() => {
		loadRacesPage();
	});

	onDestroy(() => {
		raceFilters.set({});
		racesPage.set(DEFAULT_PAGE_RESULT);
		races.set([]);
	});

	$: {
		debouncedSearchTerm && changeKeywords();
	}

	let debouncedSearchTerm = '';
	function changeKeywords() {
		races.set([]);
		racesPage.set(DEFAULT_PAGE_RESULT);
		raceFilters.update((filters) => ({ ...filters, keywords: debouncedSearchTerm }));

		loadRacesPage();
	}

	function changePage(pageNumber: number) {
		racesPage.update((page) => ({ ...page, current_page: pageNumber }));
		loadRacesPage();
	}

	function changeLeague(league: League) {
		racesPage.update((page) => ({ ...page, current_page: 0 }));
        raceFilters.update((filters) => ({ ...filters, league: league?.id }));
		loadRacesPage();
	}

	function buildQueryParams(): string {
		let query = `/api/races?page=${$racesPage.current_page}`;

		if (!!$raceFilters.keywords) {
			query += `&keywords=${$raceFilters.keywords}`;
		}

		if (!!$raceFilters.year) {
			query += `&year=${$raceFilters.year}`;
		}

		if (!!$raceFilters.league) {
			query += `&league=${$raceFilters.league}`;
		}

		return query;
	}

	let loading: boolean = false;
	async function loadRacesPage() {
		let isLastPage = $racesPage.total_pages > 0 && $racesPage.current_page + 1 == $racesPage.total_pages;
		if (loading || isLastPage) {
			return;
		}
		loading = true;

		const response = await fetch(`http://localhost:8080${buildQueryParams()}`);
		const result = (await response.json()) as Page<Race>;

		races.set(result.results);
		racesPage.set(result.pagination);

		loading = false;
	}
</script>

<div class="flex flex-col mx-auto w-4/5 py-3 space-y-3">
	<SearchRace bind:debouncedSearchTerm on:onLeagueChanged={(e) => changeLeague(e.detail)} />

	{#if $racesPage.total_records}
		<table class="table-auto w-full">
			<thead class="text-md uppercase bg-gray-900 text-white h-9">
				<tr>
					<th class="pe-3">#</th>
					<th class="text-start pe-3">Nombre</th>
					<th class="pe-3">Liga</th>
					<th class="pe-3">Fecha</th>
					<th class="pe-3" />
				</tr>
			</thead>

			<tbody>
				{#each $races as race, i}
					<tr class="even:bg-gray-200 h-8">
						<th class="pe-3">{$racesPage.current_page * $racesPage.page_size + i + 1}</th>
						<th class="text-start pe-3">{race.name}</th>
						<th class="pe-3">{race.league?.symbol || '-'}</th>
						<th class="pe-3">{race.date}</th>
						<th class="pe-3" />
					</tr>
				{/each}
			</tbody>
		</table>

		<Pagination
			totalPages={$racesPage.total_pages}
			currentPage={$racesPage.current_page}
			on:onPageChanged={(e) => changePage(e.detail)}
		/>
	{:else if loading}
		<div class="flex w-full" role="status">
			<svg
				aria-hidden="true"
				class="w-8 h-8 animate-spin text-gray-600 fill-blue-600 mx-auto"
				viewBox="0 0 100 101"
				fill="none"
				xmlns="http://www.w3.org/2000/svg"
			>
				<path
					d="M100 50.5908C100 78.2051 77.6142 100.591 50 100.591C22.3858 100.591 0 78.2051 0 50.5908C0 22.9766 22.3858 0.59082 50 0.59082C77.6142 0.59082 100 22.9766 100 50.5908ZM9.08144 50.5908C9.08144 73.1895 27.4013 91.5094 50 91.5094C72.5987 91.5094 90.9186 73.1895 90.9186 50.5908C90.9186 27.9921 72.5987 9.67226 50 9.67226C27.4013 9.67226 9.08144 27.9921 9.08144 50.5908Z"
					fill="currentColor"
				/>
				<path
					d="M93.9676 39.0409C96.393 38.4038 97.8624 35.9116 97.0079 33.5539C95.2932 28.8227 92.871 24.3692 89.8167 20.348C85.8452 15.1192 80.8826 10.7238 75.2124 7.41289C69.5422 4.10194 63.2754 1.94025 56.7698 1.05124C51.7666 0.367541 46.6976 0.446843 41.7345 1.27873C39.2613 1.69328 37.813 4.19778 38.4501 6.62326C39.0873 9.04874 41.5694 10.4717 44.0505 10.1071C47.8511 9.54855 51.7191 9.52689 55.5402 10.0491C60.8642 10.7766 65.9928 12.5457 70.6331 15.2552C75.2735 17.9648 79.3347 21.5619 82.5849 25.841C84.9175 28.9121 86.7997 32.2913 88.1811 35.8758C89.083 38.2158 91.5421 39.6781 93.9676 39.0409Z"
					fill="currentFill"
				/>
			</svg>
			<span class="sr-only">Loading...</span>
		</div>
	{:else}
		<div class="w-full text-center">No se encontraron resultados</div>
	{/if}
</div>
