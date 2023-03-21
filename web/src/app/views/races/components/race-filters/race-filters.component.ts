import { ChangeDetectionStrategy, Component, EventEmitter, Input, OnDestroy, OnInit, Output } from '@angular/core';
import { Flag, RaceFilter, Trophy } from "src/types";
import { DropdownItem } from "src/app/shared/components/dropdown/dropdown.component";
import { NG_IF } from "src/app/shared/animations";
import * as dayjs from "dayjs";
import { z } from "zod";

type FilterProperty = keyof Omit<RaceFilter, "keywords" | "participant" | "league">;
const FILTERS_KEY = 'RACE_FILTERS';
const BADGES_KEY = 'RACE_BADGES';

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

  private _filter: RaceFilter = { year: new Date().getFullYear() };
  private _badges: { key: string, value: number | string }[] = [];

  readonly DROPDOWNS_NAMES: { [T in FilterProperty]: string } = {
    trophy: 'Trofeo',
    flag: 'Bandera',
    year: 'Año',
  }

  get years() {
    const y = dayjs().year();
    return Array.from(Array(y - 2003 + 1).keys()).map(x => x + 2003).map(x => ({ id: x, name: x.toString() }));
  }

  get badges() {
    return this._badges.map(({ key, value }) => `${key}: ${value}`)
  }

  ngOnInit() {
    this.activeComponent = true;

    // load saved session filters
    this.retrieveSessionIfExists()

    this.onFilterChange.emit(this._filter);
  }

  ngOnDestroy() {
    sessionStorage.setItem(FILTERS_KEY, JSON.stringify(this._filter));
    sessionStorage.setItem(BADGES_KEY, JSON.stringify(this._badges));
    this.activeComponent = false;
  }

  selected(values: DropdownItem[], from: FilterProperty) {
    return this._filter[from] ? values.find(x => x.id === this._filter[from]) : undefined
  }

  select(from: FilterProperty, item: DropdownItem, id: number | undefined) {
    this._filter = { ...this._filter, [from]: id };
    this._badges = [...this._badges.filter(b => b.key !== this.DROPDOWNS_NAMES[from])];  // remove possible existing badge
    this._badges.push({ key: this.DROPDOWNS_NAMES[from], value: item.name });
    this.saveFiltersAndChange();
  }

  clear(from: FilterProperty) {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { [from]: _, ...filters } = this._filter;  // removes 'from' filter key
    this._filter = filters;
    this._badges = [...this._badges.filter(b => b.key !== this.DROPDOWNS_NAMES[from])];
    this.saveFiltersAndChange();
  }

  changeKeywords(keywords: string) {
    this._filter.keywords = keywords;
    this.saveFiltersAndChange();
  }

  private saveFiltersAndChange() {
    sessionStorage.setItem(FILTERS_KEY, JSON.stringify(this._filter));
    sessionStorage.setItem(BADGES_KEY, JSON.stringify(this._badges));
    this.onFilterChange.emit(this._filter);
  }

  private retrieveSessionIfExists() {
    const filter = sessionStorage.getItem(FILTERS_KEY);
    const badges = sessionStorage.getItem(BADGES_KEY);
    if (!filter) {
      this._filter = { year: new Date().getFullYear() };
      this._badges = [{ key: this.DROPDOWNS_NAMES.year, value: `${this._filter.year}` }];
      return
    }

    // load every filter field except the 'keywords'
    this._filter = z
      .object({
        trophy: z.number().min(1).optional(),
        flag: z.number().min(1).optional(),
        league: z.number().min(1).optional(),
        year: z.number().min(1).optional(),
        participant: z.number().min(1).optional(),
      }).parse(JSON.parse(filter));
    this._badges = badges
      ? z.array(z.object({ key: z.string(), value: z.number().or(z.string()) })).parse(JSON.parse(badges))
      : []  // should never happen
  }
}
