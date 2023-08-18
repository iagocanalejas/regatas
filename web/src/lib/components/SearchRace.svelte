<script lang="ts">
	import { leagues } from '$lib/stores/leagues';
	import type { League } from '$lib/types';
	import { createEventDispatcher, onMount } from 'svelte';

	let showDropdown: boolean = false;
	export let debouncedSearchTerm: string | undefined;

	onMount(() => {
		loadLeagues();
	});

	let debounceTimer: number | undefined;
	$: {
		clearTimeout(debounceTimer);
		debounceTimer = setTimeout(() => {
			debouncedSearchTerm = searchTerm;
		}, 300);
	}

	let searchTerm: string | undefined;
	function handleSearchInput(event: unknown) {
		searchTerm = (event as { target: { value: string } }).target.value;
	}

	let selectedLeague: League | undefined;
	const dispatch = createEventDispatcher();
	function changeLeague(league: League | undefined) {
		selectedLeague = league;
		showDropdown = false;
		dispatch('onLeagueChanged', league);
	}

	async function loadLeagues() {
		const response = await fetch('http://localhost:8080/api/leagues');
		const result = (await response.json()) as League[];

		leagues.set(result);
	}
</script>

<form class="w-4/5 mx-auto">
	<div class="flex">
		<div class="relative contents text-left">
			<button
				id="dropdown-button"
				class="flex-shrink-0 z-10 inline-flex items-center py-3 px-4 text-sm font-medium text-center border rounded-l-lg focus:ring-4 focus:outline-none bg-gray-700 hover:bg-gray-600 focus:ring-gray-700 text-white border-gray-600"
				type="button"
				on:click={() => (showDropdown = !showDropdown)}
			>
				{selectedLeague?.symbol || 'Liga'}
				<svg
					class="w-2.5 h-2.5 ml-2.5"
					aria-hidden="true"
					xmlns="http://www.w3.org/2000/svg"
					fill="none"
					viewBox="0 0 10 6"
				>
					<path
						stroke="currentColor"
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="m1 1 4 4 4-4"
					/>
				</svg>
			</button>

			{#if showDropdown}
				<div class="absolute left-0 mt-2 z-10 divide-y divide-gray-100 rounded-lg shadow w-80 bg-gray-700">
					<ul class="py-2 text-sm text-gray-200" aria-labelledby="dropdown-button">
						{#each $leagues.filter((l) => l.gender == 'MALE') as league}
							<li>
								<button
									type="button"
									class="inline-flex w-full px-4 py-2 hover:bg-gray-600 hover:text-white"
									on:click={() => changeLeague(league)}
								>
									{league.name}
								</button>
							</li>
						{/each}
						<hr />
						{#each $leagues.filter((l) => l.gender == 'FEMALE') as league}
							<li>
								<button
									type="button"
									class="inline-flex w-full px-4 py-2 hover:bg-gray-600 hover:text-white"
									on:click={() => changeLeague(league)}
								>
									{league.name}
								</button>
							</li>
						{/each}
					</ul>
				</div>
			{/if}
		</div>

		<div class="relative w-full">
			<input
				type="search"
				id="search-dropdown"
				class="block p-2.5 w-full z-20 text-md rounded-r-lg border-l-2 border bg-gray-700 border-l-gray-700 border-gray-600 placeholder-gray-400 text-white"
				placeholder="Buscar..."
				autocomplete="off"
				on:input={handleSearchInput}
			/>
			<button
				type="submit"
				class="absolute top-0 right-0 p-2.5 text-sm font-medium h-full text-white rounded-r-lg border border-gray-700 focus:ring-4 focus:outline-none bg-gray-700 hover:bg-gray-600 focus:ring-gray-800"
			>
				<svg class="w-4 h-4" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 20 20">
					<path
						stroke="currentColor"
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="m19 19-4-4m0-7A7 7 0 1 1 1 8a7 7 0 0 1 14 0Z"
					/>
				</svg>
				<span class="sr-only">Search</span>
			</button>
		</div>
	</div>
</form>
