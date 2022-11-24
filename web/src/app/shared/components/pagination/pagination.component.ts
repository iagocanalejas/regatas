import { ChangeDetectionStrategy, Component, EventEmitter, Input, OnDestroy, OnInit, Output } from '@angular/core';
import { DEFAULT_PAGE, PaginationConfig } from "src/types";
import { BehaviorSubject, distinct, Subject, takeWhile } from "rxjs";

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

  @Output() pageChange: EventEmitter<PaginationConfig> = new EventEmitter();

  paginationOptions = [
    { value: 25, text: '25 regatas por página' },
    { value: 50, text: '50 regatas por página' },
    { value: 100, text: '100 regatas por página' }
  ];

  page: PaginationConfig = { ...DEFAULT_PAGE };
  debouncer: Subject<PaginationConfig> = new BehaviorSubject(this.page);

  get selectedPaginationOption() {
    return this.paginationOptions.find(x => x.value === this.page.itemsPerPage)!
  }

  ngOnInit() {
    this.activeComponent = true;

    // load saved pagination
    const p = sessionStorage.getItem(`${this.key}_${PAGINATION_KEY}`);
    this.page = p ? JSON.parse(p) : this.page

    this.debouncer.next(this.page);
    this.debouncer.pipe(
      distinct(),
      takeWhile(() => this.activeComponent),
    ).subscribe(page => this.pageChange.emit(page))
  }

  ngOnDestroy() {
    this.activeComponent = false;
    sessionStorage.setItem(`${this.key}_${PAGINATION_KEY}`, JSON.stringify(this.page));
  }

  onPageChange(page: number) {
    this.page = { ...this.page, page }
    this.debouncer.next(this.page)
  }

  onItemsPerPageChange(itemsPerPage: number) {
    this.page = { ...this.page, itemsPerPage }
    this.debouncer.next(this.page)
  }
}
