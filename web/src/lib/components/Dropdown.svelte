<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import clickOutside from '$lib/directives/clickOutside';

	type Item = {
		id: number | string;
		name: string;
	};

	export let name: string;
	export let items: Item[];
	export let selected: Item | undefined = undefined;

	const dispatch = createEventDispatcher();

	let showDropdown = false;
	function change(value?: Item) {
		showDropdown = false;
		dispatch('changed', value);
	}
</script>

<div class="content relative me-4" use:clickOutside={() => (showDropdown = false)}>
	<button
		class="text-md inline-flex items-center truncate rounded-lg border-gray-600 bg-gray-700 px-5 py-2.5 text-center font-medium text-white hover:bg-gray-600"
		type="button"
		on:click={() => (showDropdown = !showDropdown)}
	>
		{selected?.name || name}
		<svg
			class="ml-2.5 h-2.5 w-2.5"
			aria-hidden="true"
			xmlns="http://www.w3.org/2000/svg"
			fill="none"
			viewBox="0 0 10 6"
		>
			<path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="m1 1 4 4 4-4" />
		</svg>
	</button>

	{#if showDropdown}
		<div class="w-85 absolute z-10 mt-2 divide-y divide-gray-100 rounded-lg bg-gray-700 shadow">
			<ul class="no-scrollbar h-96 overflow-y-scroll text-sm text-gray-200">
				<li>
					<button
						class="block w-full px-4 py-2 uppercase hover:rounded-t-lg hover:bg-gray-600 hover:text-white"
						on:click={() => change(undefined)}
					>
						{name}
					</button>
				</li>
				<hr />
				{#each items as item}
					<li>
						<button class="block w-full px-4 py-2 hover:bg-gray-600 hover:text-white" on:click={() => change(item)}>
							{item.name}
						</button>
					</li>
				{/each}
			</ul>
		</div>
	{/if}
</div>
