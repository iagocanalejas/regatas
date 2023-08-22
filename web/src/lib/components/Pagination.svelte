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
	<ul class="flex h-8 items-center -space-x-px text-sm">
		<li>
			<button
				class="ml-0 flex h-8 items-center justify-center rounded-l-lg border border-gray-700 bg-gray-800 px-3 leading-tight text-gray-400 hover:bg-gray-700 hover:text-white"
				on:click={() => changePage(currentPage - 1)}
			>
				<span class="sr-only">Previous</span>
				<svg class="h-2.5 w-2.5" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 6 10">
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
						? 'flex h-8 items-center justify-center border border-gray-700 bg-gray-700 px-3 leading-tight text-white hover:bg-blue-100 hover:text-blue-700'
						: 'flex h-8 items-center justify-center border border-gray-700 bg-gray-800 px-3 leading-tight text-gray-400 hover:bg-gray-700 hover:text-white'}
					on:click={() => changePage(i)}
				>
					{i + 1}
				</button>
			</li>
		{/each}

		<li>
			<button
				class="flex h-8 items-center justify-center rounded-r-lg border border-gray-700 bg-gray-800 px-3 leading-tight text-gray-400 hover:bg-gray-700 hover:text-white"
				on:click={() => changePage(currentPage + 1)}
			>
				<span class="sr-only">Next</span>
				<svg class="h-2.5 w-2.5" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 6 10">
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
