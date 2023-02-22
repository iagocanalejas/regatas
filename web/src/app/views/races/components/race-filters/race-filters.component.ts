import { ChangeDetectionStrategy, Component, EventEmitter, Input, OnDestroy, OnInit, Output } from '@angular/core';
import { Flag, RaceFilter, Trophy } from "src/types";
import { DropdownItem } from "src/app/shared/components/dropdown/dropdown.component";
import { BehaviorSubject, debounceTime, distinctUntilChanged, takeWhile } from "rxjs";
import { NG_IF } from "src/app/shared/animations";
import * as dayjs from "dayjs";
import { z } from "zod";

type ValidFilters = 'trophy' | 'flag' | 'year';
const FILTERS_KEY = 'RACE_FILTERS';

@Component({
  selector: 'race-filters',
  templateUrl: './race-filters.component.html',
  styleUrls: ['./race-filters.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  animations: [...NG_IF],
})
export class RaceFiltersComponent implements OnInit, OnDestroy {
  private activeComponent: boolean = false;
  @Input() trophies!: Trophy[];
  @Input() flags!: Flag[];

  @Output() onFilterChange = new EventEmitter<Partial<RaceFilter>>();

  private _filters!: RaceFilter;

  keywords: string = '';
  searching: BehaviorSubject<string> = new BehaviorSubject(this.keywords);
  showFilters: boolean = false

  get years() {
    const y = dayjs().year();
    return Array.from(Array(y - 2003 + 1).keys()).map(x => x + 2003).map(x => ({ id: x, name: x.toString() }));
  }

  get windowsWidth() {
    return window.innerWidth
  }

  ngOnInit() {
    this.activeComponent = true;

    // load saved session filters
    const f = sessionStorage.getItem(FILTERS_KEY);
    this._filters = f ? this.retrieveFilters(f) : {}
    this.onFilterChange.emit(this._filters);

    // subscribe to searchin behaviour
    this.searching.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      takeWhile(() => this.activeComponent),
    ).subscribe(keywords => {
      this._filters = { ...this._filters, keywords };
      return this.onFilterChange.emit(this._filters);
    });
  }

  ngOnDestroy() {
    sessionStorage.setItem(FILTERS_KEY, JSON.stringify(this._filters));
    this.activeComponent = false;
  }

  selected(values: DropdownItem[], from: ValidFilters) {
    return this._filters[from] ? values.find(x => x.id === this._filters[from]) : undefined
  }

  select(from: ValidFilters, id: number | undefined) {
    this._filters = { ...this._filters, [from]: id };
    this.onFilterChange.emit(this._filters);
  }

  clear(from: ValidFilters) {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { [from]: _, ...filters } = this._filters;  // removes 'from' filter key
    this._filters = filters;
    this.onFilterChange.emit(this._filters);
  }

  onKeywordsChanged() {
    this.searching.next(this.keywords);
  }

  clearKeywords() {
    this.keywords = '';
    this.onKeywordsChanged();
  }

  private retrieveFilters(filters: string): RaceFilter {
    const filterSchema = z.object({
      trophy: z.number().min(1).optional(),
      flag: z.number().min(1).optional(),
      league: z.number().min(1).optional(),
      year: z.number().min(1).optional(),
      participant_club: z.number().min(1).optional(),
      keywords: z.string().optional(),
    });
    return filterSchema.parse(JSON.parse(filters))
  }
}
