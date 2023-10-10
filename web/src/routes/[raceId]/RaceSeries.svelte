<script lang="ts">
	import ParticipantsTable from './ParticipantsTable.svelte';
	import type { Participant } from '$lib/types';

	export let series: number;
	export let laps: number;
	export let participants: Participant[];

	let expanded = false;

	function sortedParticipantsBySeries(series: number): Participant[] {
		return participants.filter((p) => p.series === series).sort((p1, p2) => p1.lane - p2.lane);
	}
</script>

<div>
	<button
		class="inline-flex w-full items-center justify-center bg-gray-700 py-2 text-white"
		on:click={() => (expanded = !expanded)}
	>
		<span class="text-center font-semibold">TIEMPOS POR TANDA</span>
		<svg
			class="ml-2.5 h-2.5 w-2.5"
			class:-rotate-90={!expanded}
			aria-hidden="true"
			xmlns="http://www.w3.org/2000/svg"
			fill="none"
			viewBox="0 0 10 6"
		>
			<path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="m1 1 4 4 4-4" />
		</svg>
	</button>

	{#if expanded}
		<div class="border border-gray-700">
			{#each { length: series } as _, i}
				<ParticipantsTable
					title={`Tanda ${i + 1}`}
					participants={sortedParticipantsBySeries(i + 1)}
					{laps}
					showLanes={true}
				/>
			{/each}
		</div>
	{/if}
</div>
