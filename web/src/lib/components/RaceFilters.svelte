<script lang="ts">
	import { raceFilters } from '$lib/stores/races';
	import { GlobalsService } from '$lib/services/globals';
	import { flags, trophies } from '$lib/stores/globals';
	import type { Flag, Trophy } from '$lib/types';
	import { createEventDispatcher, onMount } from 'svelte';
	import RaceSearch from './RaceSearch.svelte';

	const dispatch = createEventDispatcher();

	onMount(() => {
		if (!$trophies.length || !$flags.length) {
			Promise.all([GlobalsService.loadTrophies(), GlobalsService.loadFlags()]).then(([loadedTrophies, loadedFlags]) => {
				trophies.set(loadedTrophies);
				flags.set(loadedFlags);
				restoreState();
			});
		} else {
			restoreState();
		}
	});

	function restoreState() {
		if ($raceFilters.trophy) {
			selectedTrophy = $trophies.find((t) => t.id === $raceFilters.trophy);
		}
		if ($raceFilters.flag) {
			selectedFlag = $flags.find((f) => f.id === $raceFilters.flag);
		}
	}

	let showTrophiesDropdown = false;
	let showFlagsDropdown = false;
	function toggleDropdown(dropdown: 'trophy' | 'flag', open: boolean) {
		showTrophiesDropdown = dropdown === 'trophy' ? open : false;
		showFlagsDropdown = dropdown === 'flag' ? open : false;
	}

	let selectedTrophy: Trophy | undefined;
	let selectedFlag: Flag | undefined;
	function change(dropdown: 'trophy' | 'flag', value: Trophy | Flag) {
		selectedTrophy = dropdown === 'trophy' ? (value as Trophy) : selectedTrophy;
		selectedFlag = dropdown === 'flag' ? (value as Flag) : selectedFlag;

		showFlagsDropdown = false;
		showTrophiesDropdown = false;
		dispatch(`${dropdown}Changed`, value);
	}

	function clear() {
		showFlagsDropdown = false;
		showTrophiesDropdown = false;

		selectedTrophy = undefined;
		selectedFlag = undefined;
		dispatch('clear');
	}
</script>

<RaceSearch on:leagueChanged on:keywordsChanged on:yearChanged on:clear={() => clear()} />

<div class="mx-auto flex w-4/5 justify-start">
	<div class="me-4">
		<button
			class="text-md inline-flex items-center truncate rounded-lg border-gray-600 bg-gray-700 px-5 py-2.5 text-center font-medium text-white hover:bg-gray-600"
			type="button"
			on:click={() => toggleDropdown('trophy', !showTrophiesDropdown)}
		>
			{selectedTrophy?.name || 'Trophy'}
			<svg
				class="ml-2.5 h-2.5 w-2.5"
				aria-hidden="true"
				xmlns="http://www.w3.org/2000/svg"
				fill="none"
				viewBox="0 0 10 6"
			>
				<path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="m1 1 4 4 4-4" />
			</svg>
		</button>

		{#if showTrophiesDropdown}
			<div class="w-85 absolute z-10 mt-2 divide-y divide-gray-100 rounded-lg bg-gray-700 shadow">
				<ul class="h-96 overflow-y-scroll py-2 text-sm text-gray-200">
					{#each $trophies as trophy}
						<li>
							<button
								class="block px-4 py-2 hover:bg-gray-600 hover:text-white"
								on:click={() => change('trophy', trophy)}
							>
								{trophy.name}
							</button>
						</li>
					{/each}
				</ul>
			</div>
		{/if}
	</div>

	<div>
		<button
			class="text-md inline-flex items-center truncate rounded-lg border-gray-600 bg-gray-700 px-5 py-2.5 text-center font-medium text-white hover:bg-gray-600"
			type="button"
			on:click={() => toggleDropdown('flag', !showFlagsDropdown)}
		>
			{selectedFlag?.name || 'Bandera'}
			<svg
				class="ml-2.5 h-2.5 w-2.5"
				aria-hidden="true"
				xmlns="http://www.w3.org/2000/svg"
				fill="none"
				viewBox="0 0 10 6"
			>
				<path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="m1 1 4 4 4-4" />
			</svg>
		</button>

		{#if showFlagsDropdown}
			<div class="w-85 absolute z-10 mt-2 divide-y divide-gray-100 rounded-lg bg-gray-700 shadow">
				<ul class="h-96 overflow-y-scroll py-2 text-sm text-gray-200" aria-labelledby="dropdownDefaultButton">
					{#each $flags as flag}
						<li>
							<button class="block px-4 py-2 hover:bg-gray-600 hover:text-white" on:click={() => change('flag', flag)}>
								{flag.name}
							</button>
						</li>
					{/each}
				</ul>
			</div>
		{/if}
	</div>
</div>
