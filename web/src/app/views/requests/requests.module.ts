import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from "@angular/router";
import { routes } from "./requests.routes";
import { SharedModule } from "src/app/shared/shared.module";
import { RequestsService } from "./requests.service";
import { RequestsComponent } from "./components/requests.component";
import { FormEntityComponent } from './components/forms/form-entity/form-entity.component';
import { FormRaceComponent } from './components/forms/form-race/form-race.component';
import { FormParticipantComponent } from './components/forms/form-participant/form-participant.component';


@NgModule({
  declarations: [
    RequestsComponent,
    FormEntityComponent,
    FormRaceComponent,
    FormParticipantComponent,
  ],
  imports: [
    CommonModule, SharedModule,
    RouterModule.forChild(routes),
  ],
  providers: [
    RequestsService,
  ],
})
export class RequestsModule {
}
