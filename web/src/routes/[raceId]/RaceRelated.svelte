<script lang="ts">
	import { goto } from '$app/navigation';
	import type { Race } from '$lib/types';
	import { createEventDispatcher } from 'svelte';

	export let raceId: number;
	export let related: Race[];

	const dispatch = createEventDispatcher();
	function changeRace(raceId: number) {
		goto(`${raceId}`);
		dispatch('raceChanged', raceId);
	}
</script>

<div>
	<div class="flex w-full justify-center bg-gray-700 py-2 text-white">
		<span class="text-center font-semibold">REGATAS RELACIONADAS</span>
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
					class:bg-green-800={race.id === raceId}
					class:text-white={race.id === raceId}
					class:even:bg-gray-200={race.id !== raceId}
					on:click={() => changeRace(race.id)}
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
