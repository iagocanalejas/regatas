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
</script>

{#if race && race.participants}
	<table>
		<thead>
			<tr>
				<th class="pe-3">Puesto</th>
				<th class="pe-3 text-start">Club</th>
				{#each { length: race.laps || 0 } as _, i}
					<th class="pe-3">Largo {i + 1}</th>
				{/each}
			</tr>
		</thead>
		<tbody>
			{#each race.participants as participant, i}
				<tr>
					<th class="pe-3">{i + 1}</th>
					<th class="pe-3 text-start">{participant.club.raw_name || participant.club.name}</th>
					{#each { length: race.laps || 0 } as _, i}
						<th class="pe-3">{participant.laps[i]}</th>
					{/each}
				</tr>
			{/each}
		</tbody>
	</table>
{/if}
