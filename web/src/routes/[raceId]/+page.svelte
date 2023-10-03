<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import ParticipantsTable from '$lib/components/ParticipantsTable.svelte';
	import { RacesService } from '$lib/services/races';
	import type { Participant, Race } from '$lib/types';
	import { onMount } from 'svelte';

	let { raceId } = $page.params;

	let race: Race;
	let related: Race[];
	onMount(async () => await load(raceId));

	async function load(id: string) {
		raceId = id;
		if (raceId && parseInt(raceId)) {
			race = await RacesService.get(raceId);
		}
		if (race && (!related || related.length === 0)) {
			related = await RacesService.getRelated(race);
		}
	}

	function sortedParticipantsBySeries(series: number): Participant[] {
		return (race.participants || []).filter((p) => p.series === series).sort((p1, p2) => p1.lane - p2.lane);
	}
</script>

<div class="mx-auto flex w-4/5 flex-col py-3">
	{#if race && race.participants?.length}
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

	{#if related?.length}
		<div class="mt-2 flex w-full justify-center bg-gray-700 py-2 text-white">
			<span class="text-center font-semibold">Regatas relacionadas</span>
		</div>

		<table class="w-full table-auto">
			<thead class="text-md h-9 bg-gray-700 uppercase text-white">
				<tr>
					<th class="pe-3">#</th>
					<th class="pe-3 text-start">Nombre</th>
					<th class="pe-3">Fecha</th>
					<th class="pe-3" />
				</tr>
			</thead>

			<tbody>
				{#each related as race, i}
					<tr
						class="h-8"
						class:bg-green-800={race.id === +raceId}
						class:text-white={race.id === +raceId}
						class:even:bg-gray-200={race.id !== +raceId}
						on:click={() => {
							goto(`${race.id}`);
							load(`${race.id}`);
						}}
					>
						<th class="pe-3">{i + 1}</th>
						<th class="pe-3 text-start">{race.name}</th>
						<th class="pe-3">{race.date}</th>
						<th class="px-3">
							<svg
								class="h-2.5 w-2.5"
								aria-hidden="true"
								xmlns="http://www.w3.org/2000/svg"
								fill="none"
								viewBox="0 0 6 10"
							>
								<path
									stroke="currentColor"
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="m1 9 4-4-4-4"
								/>
							</svg>
						</th>
					</tr>
				{/each}
			</tbody>
		</table>
	{/if}
</div>
