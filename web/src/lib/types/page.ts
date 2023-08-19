export type Page<T> = {
	results: T[];
	pagination: PaginationResult;
};

export type PaginationResult = {
	current_page: number;
	next: string;
	page_size: number;
	total_records: number;
	total_pages: number;
};

export type PaginationConfig = {
	itemsPerPage: number;
	page: number;
	sortBy?: string;
};

export const DEFAULT_PAGE: PaginationConfig = { itemsPerPage: 30, page: 0 };
export const DEFAULT_PAGE_RESULT = {
	current_page: 0,
	next: '',
	page_size: 100,
	total_records: 0,
	total_pages: 0
};
