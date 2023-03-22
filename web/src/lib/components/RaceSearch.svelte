<script lang="ts">
	import { GlobalsService } from '$lib/services/globals';
	import { leagues } from '$lib/stores/globals';
	import type { League } from '$lib/types';
	import { createEventDispatcher, onMount } from 'svelte';

	const dispatch = createEventDispatcher();

	onMount(async () => {
		leagues.set(await GlobalsService.loadLeagues());
	});

	function years(): number[] {
		const result: number[] = [];
		for (let i = 2003; i <= new Date().getFullYear(); i++) {
			result.push(i);
		}
		return result.reverse();
	}

	let showLeaguesDropdown: boolean = false;
	let showYearDropdown: boolean = false;
	function toggleDropdown(dropdown: 'league' | 'year', open: boolean) {
		showLeaguesDropdown = dropdown === 'league' ? open : false;
		showYearDropdown = dropdown === 'year' ? open : false;
	}

	let searchTerm: string | undefined;
	let debounceTimer: number | undefined;
	$: {
		clearTimeout(debounceTimer);
		debounceTimer = setTimeout(() => dispatch('keywordsChanged', searchTerm), 300);
	}

	let selectedLeague: League | undefined;
	let selectedYear: number | undefined;
	function change(dropdown: 'league' | 'year', value: League | number) {
		selectedLeague = dropdown === 'league' ? (value as League) : selectedLeague;
		selectedYear = dropdown === 'year' ? (value as number) : selectedYear;

		showYearDropdown = false;
		showLeaguesDropdown = false;
		dispatch(`${dropdown}Changed`, value);
	}

	function clear() {
		showYearDropdown = false;
		showLeaguesDropdown = false;

		searchTerm = undefined; // TODO: this triggers two requests
		selectedYear = undefined;
		selectedLeague = undefined;
		dispatch('clear');
	}
</script>

<form class="w-4/5 mx-auto">
	<div class="flex">
		<div class="relative contents text-left">
			<button
				id="leagues-dropdown"
				class="flex-shrink-0 z-10 inline-flex items-center py-3 px-4 text-sm font-medium text-center border rounded-l-lg bg-gray-700 hover:bg-gray-600 text-white border-gray-600"
				type="button"
				on:click={() => toggleDropdown('league', !showLeaguesDropdown)}
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

			{#if showLeaguesDropdown}
				<div class="absolute mt-12 z-10 divide-y divide-gray-100 rounded-lg shadow w-80 bg-gray-700">
					<ul class="py-2 text-sm text-gray-200" aria-labelledby="leagues-dropdown">
						{#each $leagues.filter((l) => l.gender == 'MALE') as league}
							<li>
								<button
									type="button"
									class="inline-flex w-full px-4 py-2 hover:bg-gray-600 hover:text-white"
									on:click={() => change('league', league)}
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
									on:click={() => change('league', league)}
								>
									{league.name}
								</button>
							</li>
						{/each}
					</ul>
				</div>
			{/if}
		</div>

		<div class="relative contents text-left">
			<button
				id=""
				class="flex-shrink-0 z-10 inline-flex items-center py-3 px-4 text-sm font-medium text-center border bg-gray-700 hover:bg-gray-600 text-white border-gray-600"
				type="button"
				on:click={() => toggleDropdown('year', !showYearDropdown)}
			>
				{selectedYear || 'Año'}
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
			{#if showYearDropdown}
				<div class="absolute mt-12 z-10 divide-y divide-gray-100 rounded-lg shadow w-80 bg-gray-700">
					<ul class="py-2 text-sm text-gray-200" aria-labelledby="leagues-dropdown">
						{#each years() as year}
							<li>
								<button
									type="button"
									class="inline-flex w-full px-4 py-2 hover:bg-gray-600 hover:text-white"
									on:click={() => change('year', year)}
								>
									{year}
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
				bind:value={searchTerm}
			/>
			<button
				type="button"
				class="absolute top-0 right-0 p-2.5 text-sm font-medium h-full text-white rounded-r-lg border border-gray-700 bg-gray-700 hover:bg-gray-600"
				on:click={clear}
			>
				<svg class="w-4 h-4" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 14 14">
					<path
						stroke="currentColor"
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="m1 1 6 6m0 0 6 6M7 7l6-6M7 7l-6 6"
					/>
				</svg>
				<span class="sr-only">Clear</span>
			</button>
		</div>
	</div>
</form>
