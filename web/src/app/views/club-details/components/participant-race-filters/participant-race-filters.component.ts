import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import {
  category_es,
  Flag,
  Gender,
  gender_es,
  GENDERS,
  PARTICIPANT_CATEGORIES,
  ParticipantCategory,
  ParticipantFilter,
  Trophy
} from "src/types";
import { DropdownItem } from "src/app/shared/components/dropdown/dropdown.component";
import { NG_IF } from "src/app/shared/animations";
import * as dayjs from "dayjs";

type FilterProperty = keyof Omit<ParticipantFilter, "keywords">;

@Component({
  selector: 'participant-race-filters',
  templateUrl: './participant-race-filters.component.html',
  styleUrls: ['./participant-race-filters.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  animations: [...NG_IF],
})
export class ParticipantRaceFiltersComponent {
  @Input() trophies!: Trophy[];
  @Input() flags!: Flag[];

  @Output() onFilterChange = new EventEmitter<Partial<ParticipantFilter>>();

  private _filter: ParticipantFilter = {};
  private _badges: { key: string, value?: string }[] = [];

  genders: DropdownItem[] = GENDERS.map((v, i) => ({ id: i, name: v }))
  categories: DropdownItem[] = PARTICIPANT_CATEGORIES.map((v, i) => ({ id: i, name: v }))

  readonly DROPDOWNS_NAMES: { [T in FilterProperty]: string } = {
    gender: 'Género',
    category: 'Categoría',
    trophy: 'Trofeo',
    flag: 'Bandera',
    league: 'Liga',
    year: 'Año',
  }

  get years() {
    const y = dayjs().year();
    return Array.from(Array(y - 2003 + 1).keys()).map(x => x + 2003).map(x => ({ id: x, name: x.toString() }));
  }

  get badges() {
    return this._badges.map(({ key, value }) => `${key}: ${value}`)
  }

  selected(values: DropdownItem[], from: FilterProperty) {
    return this._filter[from] ? values.find(x => x.id === this._filter[from]) : undefined
  }

  select(from: FilterProperty, item: DropdownItem, key: number | string, displayName?: string) {
    this._filter = { ...this._filter, [from]: key };
    this._badges = [...this._badges.filter(b => b.key !== this.DROPDOWNS_NAMES[from])];  // remove possible existing badge
    this._badges.push({ key: this.DROPDOWNS_NAMES[from], value: displayName || item.name });
    return this.onFilterChange.emit(this._filter);
  }

  clear(from: FilterProperty) {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { [from]: _, ...filters } = this._filter;  // removes 'from' filter key
    this._filter = filters;
    this._badges = [...this._badges.filter(b => b.key !== this.DROPDOWNS_NAMES[from])];
    return this.onFilterChange.emit(this._filter);
  }

  changeKeywords(keywords: string) {
    this._filter.keywords = keywords;
    return this.onFilterChange.emit(this._filter);
  }

  readableGender = (v: string) => gender_es[v as Gender];
  readableCategory = (v: string) => category_es[v as ParticipantCategory];
}
