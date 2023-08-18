<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	export let totalPages: number;
	export let currentPage: number;

	const dispatch = createEventDispatcher();
	function changePage(page: number) {
		if (page < 0 || page >= totalPages) {
			return;
		}
		dispatch('onPageChanged', page);
	}
</script>

<nav aria-label="Races navigation" class="mx-auto">
	<ul class="flex items-center -space-x-px h-8 text-sm">
		<li>
			<button
				class="flex items-center justify-center px-3 h-8 ml-0 leading-tight border rounded-l-lg bg-gray-800 border-gray-700 text-gray-400 hover:bg-gray-700 hover:text-white"
				on:click={() => changePage(currentPage - 1)}
			>
				<span class="sr-only">Previous</span>
				<svg class="w-2.5 h-2.5" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 6 10">
					<path
						stroke="currentColor"
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M5 1 1 5l4 4"
					/>
				</svg>
			</button>
		</li>

		{#each { length: totalPages } as _, i}
			<li>
				<button
					class={currentPage === i
						? 'flex items-center justify-center px-3 h-8 leading-tight border bg-gray-700 border-gray-700 text-white hover:bg-blue-100 hover:text-blue-700'
						: 'flex items-center justify-center px-3 h-8 leading-tight border bg-gray-800 border-gray-700 text-gray-400 hover:bg-gray-700 hover:text-white'}
					on:click={() => changePage(i)}
				>
					{i + 1}
				</button>
			</li>
		{/each}

		<li>
			<button
				class="flex items-center justify-center px-3 h-8 leading-tight border rounded-r-lg bg-gray-800 border-gray-700 text-gray-400 hover:bg-gray-700 hover:text-white"
				on:click={() => changePage(currentPage + 1)}
			>
				<span class="sr-only">Next</span>
				<svg class="w-2.5 h-2.5" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 6 10">
					<path
						stroke="currentColor"
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="m1 9 4-4-4-4"
					/>
				</svg>
			</button>
		</li>
	</ul>
</nav>
