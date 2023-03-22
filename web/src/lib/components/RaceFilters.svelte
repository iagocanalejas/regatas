<script lang="ts">
	import { GlobalsService } from '$lib/services/globals';
	import { flags, trophies } from '$lib/stores/globals';
	import type { Flag, Trophy } from '$lib/types';
	import { createEventDispatcher, onMount } from 'svelte';
	import RaceSearch from './RaceSearch.svelte';

	const dispatch = createEventDispatcher();

	onMount(async () => {
		trophies.set(await GlobalsService.loadTrophies());
		flags.set(await GlobalsService.loadFlags());
	});

	let showTrophiesDropdown: boolean = false;
	let showFlagsDropdown: boolean = false;
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

<div class="flex justify-center w-4/5 mx-auto">
	<div class="me-4">
		<button
			class="text-white truncate font-medium rounded-lg text-md px-5 py-2.5 text-center inline-flex items-center bg-gray-700 hover:bg-gray-600 border-gray-600"
			type="button"
			on:click={() => toggleDropdown('trophy', !showTrophiesDropdown)}
		>
			{selectedTrophy?.name || 'Trophy'}
			<svg
				class="w-2.5 h-2.5 ml-2.5"
				aria-hidden="true"
				xmlns="http://www.w3.org/2000/svg"
				fill="none"
				viewBox="0 0 10 6"
			>
				<path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="m1 1 4 4 4-4" />
			</svg>
		</button>

		{#if showTrophiesDropdown}
			<div class="absolute mt-2 z-10 divide-y divide-gray-100 rounded-lg shadow w-85 bg-gray-700">
				<ul class="py-2 text-sm text-gray-200 h-96 overflow-y-scroll">
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
			class="text-white truncate font-medium rounded-lg text-md px-5 py-2.5 text-center inline-flex items-center bg-gray-700 hover:bg-gray-600 border-gray-600"
			type="button"
			on:click={() => toggleDropdown('flag', !showFlagsDropdown)}
		>
			{selectedFlag?.name || 'Bandera'}
			<svg
				class="w-2.5 h-2.5 ml-2.5"
				aria-hidden="true"
				xmlns="http://www.w3.org/2000/svg"
				fill="none"
				viewBox="0 0 10 6"
			>
				<path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="m1 1 4 4 4-4" />
			</svg>
		</button>

		{#if showFlagsDropdown}
			<div class="absolute mt-2 z-10 divide-y divide-gray-100 rounded-lg shadow w-85 bg-gray-700">
				<ul class="py-2 text-sm text-gray-200 h-96 overflow-y-scroll" aria-labelledby="dropdownDefaultButton">
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
