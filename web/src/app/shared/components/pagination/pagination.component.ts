import { ChangeDetectionStrategy, Component, EventEmitter, Input, OnDestroy, OnInit, Output } from '@angular/core';
import { DEFAULT_PAGE, PaginationConfig } from "src/types";
import { distinct, ReplaySubject, takeWhile } from "rxjs";
import { z } from "zod";

const PAGINATION_KEY = 'PAGINATION';

@Component({
  selector: 'pagination',
  templateUrl: './pagination.component.html',
  styleUrls: ['./pagination.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class PaginationComponent implements OnInit, OnDestroy {
  private activeComponent: boolean = false;
  @Input() key: string = `${Math.floor(Math.random() * 1000)}`;
  @Input() collectionSize!: number;

  @Output() onPageChange: EventEmitter<PaginationConfig> = new EventEmitter();

  paginationOptions = [
    { value: 25, text: '25 regatas por página' },
    { value: 50, text: '50 regatas por página' },
    { value: 100, text: '100 regatas por página' },
    { value: 250, text: '250 regatas por página' },
    { value: 500, text: '500 regatas por página' },
  ];

  page!: PaginationConfig;
  debouncer = new ReplaySubject<PaginationConfig>();

  get selectedPaginationOption() {
    return this.paginationOptions.find(x => x.value === this.page.itemsPerPage)
  }

  ngOnInit() {
    this.activeComponent = true;

    // load saved pagination
    const p = sessionStorage.getItem(`${this.key}_${PAGINATION_KEY}`);
    this.page = p ? this.retrievePage(p) : { ...DEFAULT_PAGE }

    this.debouncer.pipe(
      distinct(({itemsPerPage, page}) => `${itemsPerPage}|${page}`),
      takeWhile(() => this.activeComponent),
    ).subscribe(page => {
      sessionStorage.setItem(`${this.key}_${PAGINATION_KEY}`, JSON.stringify(this.page));
      return this.onPageChange.emit(page)
    })

    this.debouncer.next(this.page);
  }

  ngOnDestroy() {
    this.activeComponent = false;
    sessionStorage.setItem(`${this.key}_${PAGINATION_KEY}`, JSON.stringify(this.page));
  }

  changePage(page: number) {
    this.page = { ...this.page, page }
    this.debouncer.next(this.page)
  }

  changeItemsPerPage(itemsPerPage: number) {
    this.page = { ...this.page, itemsPerPage }
    this.debouncer.next(this.page)
  }

  private retrievePage(page: string): PaginationConfig {
    const pageSchema = z.object({
      itemsPerPage: z.number().min(1),
      page: z.number().min(0),
      sortBy: z.string().optional(),
    });
    return pageSchema.parse(JSON.parse(page))
  }
}
