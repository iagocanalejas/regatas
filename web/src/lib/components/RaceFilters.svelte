<script lang="ts">
	import { raceFilters } from '$lib/stores/races';
	import { GlobalsService } from '$lib/services/globals';
	import { flags, trophies, clubs } from '$lib/stores/globals';
	import type { Entity, Flag, Trophy } from '$lib/types';
	import { createEventDispatcher, onMount } from 'svelte';
	import RaceSearch from './RaceSearch.svelte';
	import Dropdown from './Dropdown.svelte';

	const dispatch = createEventDispatcher();

	onMount(() => {
		if (!$trophies.length || !$flags.length || !$clubs.length) {
			Promise.all([GlobalsService.loadTrophies(), GlobalsService.loadFlags(), GlobalsService.loadClubs()]).then(
				([loadedTrophies, loadedFlags, loadedClubs]) => {
					trophies.set(loadedTrophies);
					flags.set(loadedFlags);
					clubs.set(loadedClubs);
					restoreState();
				}
			);
		} else {
			restoreState();
		}
	});

	function restoreState() {
		selectedTrophy = $raceFilters.trophy ? $trophies.find((t) => t.id === $raceFilters.trophy) : undefined;
		selectedFlag = $raceFilters.flag ? $flags.find((f) => f.id === $raceFilters.flag) : undefined;
		selectedClub = $raceFilters.participant ? $clubs.find((c) => c.id === $raceFilters.participant) : undefined;
	}

	let selectedTrophy: Trophy | undefined;
	let selectedFlag: Flag | undefined;
	let selectedClub: Entity | undefined;
	function change(dropdown: 'trophy' | 'flag' | 'participant', value?: Trophy | Flag) {
		selectedTrophy = dropdown === 'trophy' ? (value as Trophy) : selectedTrophy;
		selectedFlag = dropdown === 'flag' ? (value as Flag) : selectedFlag;
		selectedClub = dropdown === 'participant' ? (value as Entity) : selectedClub;

		dispatch(`${dropdown}Changed`, value);
	}

	function clear() {
		selectedTrophy = undefined;
		selectedFlag = undefined;
		selectedClub = undefined;

		dispatch('clear');
	}
</script>

<RaceSearch on:leagueChanged on:keywordsChanged on:yearChanged on:clear={() => clear()} />

<div class="mx-auto flex w-4/5 justify-start">
	<Dropdown name="Trofeo" items={$trophies} selected={selectedTrophy} on:changed={(e) => change('trophy', e.detail)} />
	<Dropdown name="Bandera" items={$flags} selected={selectedFlag} on:changed={(e) => change('flag', e.detail)} />
	<Dropdown name="Club" items={$clubs} selected={selectedClub} on:changed={(e) => change('participant', e.detail)} />
</div>
