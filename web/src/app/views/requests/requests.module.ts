import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from "@angular/router";
import { routes } from "./requests.routes";
import { RequestsService } from "./requests.service";
import { RequestsComponent } from "./components/requests.component";
import { FormEntityComponent } from './components/forms/form-entity/form-entity.component';
import { FormRaceComponent } from './components/forms/form-race/form-race.component';
import { FormParticipantComponent } from './components/forms/form-participant/form-participant.component';
import { FormsModule, ReactiveFormsModule } from "@angular/forms";
import { FormlyBootstrapModule } from "@ngx-formly/bootstrap";
import { FormlyModule } from "@ngx-formly/core";
import { RepeatTypeComponent } from "./components/forms/repeat-type.component";


@NgModule({
  declarations: [
    RepeatTypeComponent,
    RequestsComponent,
    FormEntityComponent,
    FormRaceComponent,
    FormParticipantComponent,
  ],
  imports: [
    CommonModule, FormsModule, ReactiveFormsModule,
    FormlyBootstrapModule,
    FormlyModule.forRoot({
      types: [{ name: 'repeat', component: RepeatTypeComponent }],
    }),
    RouterModule.forChild(routes),
  ],
  providers: [
    RequestsService,
  ],
})
export class RequestsModule {
}
