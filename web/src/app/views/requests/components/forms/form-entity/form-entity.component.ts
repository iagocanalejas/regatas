import { ChangeDetectionStrategy, Component, EventEmitter, Output } from '@angular/core';
import { FormlyFieldConfig } from "@ngx-formly/core";
import { FormGroup } from "@angular/forms";
import { Request } from "src/types";

interface FormModel {
  name?: string;
}

@Component({
  selector: 'form-entity',
  templateUrl: './form-entity.component.html',
  styleUrls: ['./form-entity.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FormEntityComponent {
  @Output() onRequest: EventEmitter<Request> = new EventEmitter<Request>();

  form = new FormGroup({});
  model: FormModel = {};
  fields: FormlyFieldConfig[] = [
    {
      key: 'name',
      type: 'input',
      props: {
        label: 'Nombre del Club',
        placeholder: 'Nombre del Club',
        required: true,
      }
    }
  ];

  onSubmit(model: FormModel) {
    if (!model.name) return
    this.onRequest.emit({
      model: "ENTITY",
      type: "CREATE",
      changes: [{ key: 'name', value: model.name }],
    });
  }
}
