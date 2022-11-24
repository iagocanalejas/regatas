export interface Page<T> {
  results: T[];
  count: number;
  next: string;
  previous: string;
}

export interface PaginationConfig {
  itemsPerPage: number;
  page: number;
}

export const DEFAULT_PAGE: PaginationConfig = { itemsPerPage: 25, page: 0 };
export const DEFAULT_PAGE_RESULT = <T>() => ({ count: 0, next: '', previous: '', results: <T[]>[] });
