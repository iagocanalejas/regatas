<script lang="ts">
	import { page } from '$app/stores';
	import { RacesService } from '$lib/services/races';
	import type { Race } from '$lib/types';
	import { onMount } from 'svelte';

	const { raceId } = $page.params;

	let race: Race;
	onMount(async () => {
		if (raceId && parseInt(raceId)) {
			race = await RacesService.get(raceId);
		}
	});

	let showingLapTime = false;
</script>

<div class="mx-auto flex w-4/5 flex-col py-3">
	{#if race && race.participants}
		<div class="flex h-9 justify-between bg-gray-700 text-white">
			<spam class="text-md my-auto ms-4 font-semibold uppercase">Tiempos</spam>
			<div class="my-auto me-4">
				<button on:click={() => (showingLapTime = !showingLapTime)}>
					{#if showingLapTime}
						<svg
							xmlns="http://www.w3.org/2000/svg"
							width="24"
							height="24"
							viewBox="0 0 24 24"
							fill="none"
							stroke="#ffffff"
							stroke-width="2"
							stroke-linecap="round"
							stroke-linejoin="round"
						>
							<path d="M17 2.1l4 4-4 4" />
							<path d="M3 12.2v-2a4 4 0 0 1 4-4h12.8M7 21.9l-4-4 4-4" />
							<path d="M21 11.8v2a4 4 0 0 1-4 4H4.2" />
						</svg>
					{:else}
						<svg
							xmlns="http://www.w3.org/2000/svg"
							width="24"
							height="24"
							viewBox="0 0 24 24"
							fill="none"
							stroke="#ffffff"
							stroke-width="2"
							stroke-linecap="round"
							stroke-linejoin="round"
						>
							<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"></path>
							<line x1="4" y1="22" x2="4" y2="15"></line>
						</svg>
					{/if}
				</button>
			</div>
		</div>
		<table>
			<thead>
				<tr class="text-md h-9 bg-gray-700 uppercase text-white">
					<th class="pe-3">Puesto</th>
					<th class="pe-3 text-start">Club</th>
					{#if showingLapTime}
						{#each { length: race.laps || 0 } as _, i}
							<th class="pe-3">
								Largo {i + 1}
							</th>
						{/each}
					{:else}
						{#each { length: (race.laps && race.laps - 1) || 0 } as _, i}
							<th class="pe-3">
								Ciaboga {i + 1}
							</th>
						{/each}
						<th class="pe-3"> Tiempo </th>
					{/if}
				</tr>
			</thead>
			<tbody>
				{#each race.participants as participant, i}
					<tr>
						<th class="pe-3">{i + 1}</th>
						<th class="pe-3 text-start">{participant.club.raw_name || participant.club.name}</th>
						{#if showingLapTime}
							{#each { length: race.laps || 0 } as _, i}
								<th class="pe-3">
									{participant.times_per_lap[i]}
								</th>
							{/each}
						{:else}
							{#each { length: (race.laps && race.laps - 1) || 0 } as _, i}
								<th class="pe-3">{participant.laps[i]}</th>
							{/each}
							<th class="pe-3">{participant.raw_time}</th>
						{/if}
					</tr>
				{/each}
			</tbody>
		</table>
	{/if}
</div>
