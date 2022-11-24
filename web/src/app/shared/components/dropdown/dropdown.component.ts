import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';

export interface DropdownItem {
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
  @Input() nullItem?: string = undefined;
  @Input() items: T[] = [];
  @Input() showClear: boolean = false;
  @Input() selectedItem?: T = undefined;

  @Output() onSelect: EventEmitter<T | undefined> = new EventEmitter();
  @Output() onClear: EventEmitter<void> = new EventEmitter();

  select(item?: T) {
    this.selectedItem = item
    this.onSelect.emit(item)
  }

  clear() {
    this.selectedItem = undefined;
    this.onClear.emit()
  }
}
