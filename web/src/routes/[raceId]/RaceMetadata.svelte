<script lang="ts">
	import type { RaceDatasource } from '$lib/types';

	export let datasources: RaceDatasource[];

	function getImageByDatasource(datasource: string, format: 'webp' | 'jpg'): string | undefined {
		if (datasource.toUpperCase() === 'ACT') {
			return `/assets/acttv.${format}`;
		}

		if (datasource.toUpperCase() === 'LGT') {
			return `/assets/lgt.${format}`;
		}

		if (datasource.toUpperCase() === 'TRAINERAS') {
			return `/assets/traineras.${format}`;
		}

		return undefined;
	}
</script>

<div class="flex flex-row justify-center gap-x-3">
	{#each datasources as metadata}
		<a href={metadata.values.details_page} target="_blank">
			<picture>
				<source srcset={getImageByDatasource(metadata.datasource_name, 'webp')} />
				<img class="max-h-16" alt="Enlace de referencia" src={getImageByDatasource(metadata.datasource_name, 'jpg')} />
			</picture>
		</a>
	{/each}
</div>
