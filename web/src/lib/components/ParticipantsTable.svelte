<script lang="ts">
	import { ParticipantUtils, type Participant } from '$lib/types';

	export let title: string;
	export let laps = 0;
	export let showLanes = false;
	export let showSpeed = false;
	export let participants: Participant[] = [];

	let showingLapTime = false;
</script>

<div class="flex h-9 justify-between bg-gray-700 text-white">
	<spam class="text-md my-auto ms-4 font-semibold uppercase">{title}</spam>
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
<table class="w-full">
	<thead>
		<tr class="text-md h-9 bg-gray-700 uppercase text-white">
			<th class="pe-3">{showLanes ? 'Boya' : 'Puesto'}</th>
			<th class="pe-3 text-start">Club</th>
			{#if showingLapTime}
				{#each { length: laps } as _, i}
					<th class="pe-3">
						Largo {i + 1}
					</th>
				{/each}
			{:else}
				{#each { length: laps - 1 } as _, i}
					<th class="pe-3">
						Ciaboga {i + 1}
					</th>
				{/each}
				<th class="pe-3">Tiempo</th>
			{/if}
			{#if showSpeed}
				<th class="pe-3">Velocidad</th>
			{/if}
		</tr>
	</thead>
	<tbody>
		{#each participants as participant, i}
			<tr>
				<th class="pe-3">{showLanes ? participant.lane : i + 1}</th>
				<th class="pe-3 text-start">{participant.club.raw_name || participant.club.name}</th>
				{#if showingLapTime}
					{#each { length: laps } as _, i}
						<th class="pe-3">
							{participant.times_per_lap[i]}
						</th>
					{/each}
				{:else}
					{#each { length: laps - 1 } as _, i}
						<th class="pe-3">{participant.laps[i]}</th>
					{/each}
					<th class="pe-3">{participant.raw_time}</th>
				{/if}
				{#if showSpeed}
					<th class="pe-3">{ParticipantUtils.speed(participant).toLocaleString('es')} km/h</th>
				{/if}
			</tr>
		{/each}
	</tbody>
</table>
