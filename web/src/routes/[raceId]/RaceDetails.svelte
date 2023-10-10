<script lang="ts">
	import type { Race } from '$lib/types';
	import ParticipantsTable from './ParticipantsTable.svelte';
	import RaceSeries from './RaceSeries.svelte';

	export let race: Race | undefined;
</script>

{#if race && race.participants?.length}
	<div>
		<div class="flex w-full justify-center bg-gray-700 py-2 text-white">
			<span class="text-center font-semibold">
				{race.name} ({race.date})
			</span>
		</div>
		<div class="border border-gray-700">
			<ParticipantsTable title={'Tiempos'} participants={race.participants} laps={race.laps || 0} showSpeed={true} />
		</div>
	</div>
{/if}

{#if race && race.participants?.length && (race.series || 0) > 1}
	<RaceSeries series={race.series || 0} laps={race.laps || 0} participants={race.participants} />
{/if}
