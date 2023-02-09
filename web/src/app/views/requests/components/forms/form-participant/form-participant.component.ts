import { ChangeDetectionStrategy, Component, EventEmitter, Output } from '@angular/core';
import { Request } from "src/types";
import { AbstractControl, FormGroup } from "@angular/forms";
import { FormlyFieldConfig } from "@ngx-formly/core";
import * as dayjs from "dayjs";

interface FormModel {
  name: string;
  distance?: number;
  laps?: string[];
  lane?: number;
  series?: number;
  disqualified?: boolean;
  // TODO: disqualification_reasons
}

@Component({
  selector: 'form-participant',
  templateUrl: './form-participant.component.html',
  styleUrls: ['./form-participant.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FormParticipantComponent {
  @Output() onRequest: EventEmitter<Request> = new EventEmitter<Request>();

  form = new FormGroup({});
  model: FormModel = {} as FormModel;
  fields: FormlyFieldConfig[] = [
    {
      key: 'name',
      type: 'input',
      props: {
        label: 'Nombre',
        placeholder: 'Nombre',
        required: true,
      }
    },
    {
      fieldGroupClassName: 'row',
      fieldGroup: [
        {
          key: 'distance',
          className: 'col-4',
          type: 'input',
          props: {
            type: 'number',
            label: 'Distancia',
          }
        },
        {
          key: 'lane',
          className: 'col-4',
          type: 'input',
          props: {
            type: 'number',
            label: 'Calle',
            min: 1,
            max: 10,
          }
        },
        {
          key: 'series',
          className: 'col-4',
          type: 'input',
          props: {
            type: 'number',
            label: 'Tanda',
            min: 1,
            max: 10,
          }
        },
      ],
    },
    {
      key: 'laps',
      type: 'repeat',
      props: {
        addText: 'Añadir Vuelta',
        label: 'Vueltas',
      },
      fieldArray: {
        type: 'input',
        props: {
          placeholder: 'MM:SS.mmm',
          required: true,
        },
        validators: {
          laps: {
            expression: (c: AbstractControl) => dayjs(c.value, 'mm:ss', true).isValid()
              || dayjs(c.value, 'mm:ss.SSS', true).isValid(),
            message: () => "Vuelta no valida",
          },
        },
      },
    },
  ];

  onSubmit(model: FormModel) {
    this.onRequest.emit({
      model: "PARTICIPANT",
      type: "CREATE",
      changes: Object.entries(model).map(([key, value]) => ({ key, value })),
    });
  }
}
