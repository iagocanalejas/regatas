import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DropdownComponent } from './components/dropdown/dropdown.component';
import { NgbDropdownModule, NgbPaginationModule } from "@ng-bootstrap/ng-bootstrap";
import { PaginationComponent } from "./components/pagination/pagination.component";
import { FormsModule, ReactiveFormsModule } from "@angular/forms";
import { RaceListComponent } from "./components/lists/race-list/race-list.component";
import { RepeatTypeComponent } from "./components/forms/repeat-type.component";
import { FormlyModule } from "@ngx-formly/core";
import { FormlyBootstrapModule } from "@ngx-formly/bootstrap";

const components = [
  DropdownComponent,
  PaginationComponent,
  RaceListComponent,
  RepeatTypeComponent,
];

@NgModule({
  declarations: [
    ...components
  ],
  imports: [
    CommonModule, FormsModule, NgbDropdownModule, NgbPaginationModule,
    ReactiveFormsModule, FormlyBootstrapModule,
    FormlyModule.forRoot({
      types: [{ name: 'repeat', component: RepeatTypeComponent }],
    }),
  ],
  exports: [
    ...components,
    ReactiveFormsModule, FormlyModule, FormlyBootstrapModule,
  ],
})
export class SharedModule {
}
