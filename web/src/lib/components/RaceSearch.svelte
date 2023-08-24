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

	let showLeaguesDropdown = false;
	let showYearDropdown = false;
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

<form class="mx-auto w-4/5">
	<div class="flex">
		<div class="relative contents text-left">
			<button
				id="leagues-dropdown"
				class="z-10 inline-flex flex-shrink-0 items-center rounded-l-lg border border-gray-600 bg-gray-700 px-4 py-3 text-center text-sm font-medium text-white hover:bg-gray-600"
				type="button"
				on:click={() => toggleDropdown('league', !showLeaguesDropdown)}
			>
				{selectedLeague?.symbol || 'Liga'}
				<svg
					class="ml-2.5 h-2.5 w-2.5"
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
				<div class="absolute z-10 mt-12 w-80 divide-y divide-gray-100 rounded-lg bg-gray-700 shadow">
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
				class="z-10 inline-flex flex-shrink-0 items-center border border-gray-600 bg-gray-700 px-4 py-3 text-center text-sm font-medium text-white hover:bg-gray-600"
				type="button"
				on:click={() => toggleDropdown('year', !showYearDropdown)}
			>
				{selectedYear || 'Año'}
				<svg
					class="ml-2.5 h-2.5 w-2.5"
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
				<div class="absolute z-10 mt-12 w-80 divide-y divide-gray-100 rounded-lg bg-gray-700 shadow">
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
				class="text-md z-20 block w-full rounded-r-lg border border-l-2 border-gray-600 border-l-gray-700 bg-gray-700 p-2.5 text-white placeholder-gray-400"
				placeholder="Buscar..."
				autocomplete="off"
				bind:value={searchTerm}
			/>
			<button
				type="button"
				class="absolute right-0 top-0 h-full rounded-r-lg border border-gray-700 bg-gray-700 p-2.5 text-sm font-medium text-white hover:bg-gray-600"
				on:click={clear}
			>
				<svg class="h-4 w-4" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 14 14">
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
