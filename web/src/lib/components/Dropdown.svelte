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

	let searchTerm = '';
	let filteredItems: Item[] = [];
	$: {
		filteredItems = items.filter((i) => i.name.includes(searchTerm.toUpperCase()));
	}

	let showDropdown = false;
	function toggle(show: boolean) {
		showDropdown = show;
		if (!show) {
			searchTerm = '';
		}
	}

	function change(value?: Item) {
		toggle(false);
		dispatch('changed', value);
	}
</script>

<div class="content relative me-4" use:clickOutside={() => toggle(false)}>
	<button
		class="text-md inline-flex items-center truncate rounded-lg border-gray-600 bg-gray-700 px-5 py-2.5 text-center font-medium text-white hover:bg-gray-600"
		type="button"
		on:click={() => toggle(!showDropdown)}
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
			<div class="p-3">
				<label for="input-group-search" class="sr-only">Search</label>
				<div class="relative">
					<div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
						<svg
							class="h-4 w-4 text-gray-500 dark:text-gray-400"
							aria-hidden="true"
							xmlns="http://www.w3.org/2000/svg"
							fill="none"
							viewBox="0 0 20 20"
						>
							<path
								stroke="currentColor"
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="m19 19-4-4m0-7A7 7 0 1 1 1 8a7 7 0 0 1 14 0Z"
							/>
						</svg>
					</div>
					<input
						type="text"
						id="input-group-search"
						class="block w-full rounded-lg border border-gray-300 bg-gray-50 p-2 pl-10 text-sm text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-500 dark:bg-gray-600 dark:text-white dark:placeholder-gray-400 dark:focus:border-blue-500 dark:focus:ring-blue-500"
						placeholder="Buscar..."
						autocomplete="off"
						bind:value={searchTerm}
					/>
				</div>
			</div>

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
				{#each filteredItems as item}
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
