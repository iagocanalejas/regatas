import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { EmptyViewComponent } from "./empty-view.component";

@NgModule({
  declarations: [
    EmptyViewComponent
  ],
  imports: [
    CommonModule
  ],
  exports: [
    EmptyViewComponent
  ],
})
export class EmptyViewModule {
}
