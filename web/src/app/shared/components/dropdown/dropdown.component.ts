import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';

export type DropdownItem = {
  id: number;
  name: string;
}

@Component({
  selector: 'dropdown',
  templateUrl: './dropdown.component.html',
  styleUrls: ['./dropdown.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class DropdownComponent<T extends DropdownItem> {
  @Input() title: string = 'Dropdown';
  @Input() items: readonly T[] = [];
  @Input() hideClear: boolean = false;
  @Input() selectedItem?: T;
  @Input() displayFn: (t: string) => string = (t) => t;

  @Output() onSelect: EventEmitter<T> = new EventEmitter();
  @Output() onClear: EventEmitter<void> = new EventEmitter();

  select(item: T) {
    this.selectedItem = item
    this.onSelect.emit(item)
  }

  clear() {
    this.selectedItem = undefined;
    this.onClear.emit()
  }
}
