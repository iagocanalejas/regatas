import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DropdownComponent } from './dropdown.component';
import { NgbDropdownModule } from "@ng-bootstrap/ng-bootstrap";

@NgModule({
  declarations: [
    DropdownComponent
  ],
  imports: [
    CommonModule, NgbDropdownModule
  ],
  exports: [
    DropdownComponent
  ],
})
export class DropdownModule {
}
