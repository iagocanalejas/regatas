import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NgbDropdownModule, NgbPaginationModule } from "@ng-bootstrap/ng-bootstrap";
import { PaginationComponent } from "./pagination.component";

@NgModule({
  declarations: [
    PaginationComponent
  ],
  imports: [
    CommonModule, NgbPaginationModule, NgbDropdownModule
  ],
  exports: [
    PaginationComponent
  ],
})
export class PaginationModule {
}
