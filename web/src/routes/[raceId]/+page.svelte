<script lang="ts">
	import { page } from '$app/stores';
	import { RacesService } from '$lib/services/races';
	import type { Race } from '$lib/types';
	import { onMount } from 'svelte';
	import RaceMetadata from './RaceMetadata.svelte';
	import RaceDetails from './RaceDetails.svelte';
	import RaceRelated from './RaceRelated.svelte';

	let { raceId } = $page.params;

	let race: Race | undefined;
	let associated: Race | undefined;
	let related: Race[];
	onMount(async () => await load(raceId));

	async function load(id: string) {
		reset();

		raceId = id;
		if (raceId && parseInt(raceId)) {
			race = await RacesService.get(raceId);
		}
		if (race) {
			[associated, related] = await Promise.all([
				race.associated?.id ? RacesService.get(race.associated.id) : Promise.resolve(undefined),
				!related || related.length === 0 ? RacesService.getRelated(race) : Promise.resolve([])
			]);
		}
	}

	function reset() {
		race = undefined;
		associated = undefined;
		related = [];
	}
</script>

<div class="mx-auto mt-2 flex w-4/5 flex-col gap-y-4">
	<RaceDetails {race} />
	<RaceDetails race={associated} />

	{#if related?.length}
		<RaceRelated {related} raceId={+raceId} on:raceChanged={(e) => load(e.detail)} />
	{/if}

	{#if race?.metadata?.datasource && race.metadata.datasource.length > 0}
		<RaceMetadata datasources={race.metadata.datasource} />
	{/if}
</div>
