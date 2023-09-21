<script lang="ts">
	import { page } from '$app/stores';
	import ParticipantsTable from '$lib/components/ParticipantsTable.svelte';
	import { RacesService } from '$lib/services/races';
	import type { Participant, Race } from '$lib/types';
	import { onMount } from 'svelte';

	const { raceId } = $page.params;

	let race: Race;
	onMount(async () => {
		if (raceId && parseInt(raceId)) {
			race = await RacesService.get(raceId);
		}
	});

	function sortedParticipantsBySeries(series: number): Participant[] {
		return (race.participants || []).filter((p) => p.series === series).sort((p1, p2) => p1.lane - p2.lane);
	}
</script>

<div class="mx-auto flex w-4/5 flex-col py-3">
	{#if race && race.participants}
		<div class="my-2 flex w-full justify-center bg-gray-700 py-2 text-white">
			<span class="text-center font-semibold">
				{race.name} ({race.date})
			</span>
		</div>

		{#if (race.series || 0) > 1}
			{#each { length: race.series || 0 } as _, i}
				<div class="my-4">
					<ParticipantsTable
						title={`Tanda ${i + 1}`}
						participants={sortedParticipantsBySeries(i + 1)}
						laps={race.laps || 0}
						showLanes={true}
					/>
				</div>
			{/each}
		{/if}

		<div class="my-4">
			<ParticipantsTable title={'Tiempos'} participants={race.participants} laps={race.laps || 0} showSpeed={true} />
		</div>
	{/if}
</div>
