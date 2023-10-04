<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import ParticipantsTable from '$lib/components/ParticipantsTable.svelte';
	import { RacesService } from '$lib/services/races';
	import type { Race } from '$lib/types';
	import { onMount } from 'svelte';
	import RaceSeries from './RaceSeries.svelte';

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

<div class="mx-auto flex w-4/5 flex-col gap-y-4">
	{#if race && race.participants?.length}
		<div>
			<div class="mt-2 flex w-full justify-center bg-gray-700 py-2 text-white">
				<span class="text-center font-semibold">
					{race.name} ({race.date})
				</span>
			</div>
			<div class="border border-gray-700">
				<ParticipantsTable title={'Tiempos'} participants={race.participants} laps={race.laps || 0} showSpeed={true} />
			</div>
		</div>
	{/if}

	{#if race && race.participants?.length}
		<RaceSeries series={race.series || 0} laps={race.laps || 0} participants={race.participants} />
	{/if}

	{#if associated && associated.participants?.length}
		<div>
			<div class="flex w-full justify-center bg-gray-700 py-2 text-white">
				<span class="text-center font-semibold">
					{associated.name} ({associated.date})
				</span>
			</div>

			<div class="border border-gray-700">
				<ParticipantsTable
					title={'Tiempos'}
					participants={associated.participants}
					laps={associated.laps || 0}
					showSpeed={true}
				/>
			</div>
		</div>
	{/if}

	{#if associated && associated.participants?.length}
		<RaceSeries series={associated.series || 0} laps={associated.laps || 0} participants={associated.participants} />
	{/if}

	{#if related?.length}
		<div>
			<div class="flex w-full justify-center bg-gray-700 py-2 text-white">
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
		</div>
	{/if}
</div>
