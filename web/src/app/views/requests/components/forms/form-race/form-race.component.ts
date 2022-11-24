import { ChangeDetectionStrategy, Component, EventEmitter, Output } from '@angular/core';
import { Request } from "src/types";
import { AbstractControl, FormGroup, ValidationErrors } from "@angular/forms";
import { FormlyFieldConfig } from "@ngx-formly/core";
import * as moment from "moment";

interface FormModel {
  name: string;
  date: string;
  edition?: number;
  type: string;
  laps?: number;
  lanes?: number;
  organizer?: string;
  town?: string;
  cancelled?: boolean;
  // TODO: cancellation_reasons
}

export function DateValidator(control: AbstractControl): ValidationErrors | null {
  return moment(control.value, 'DD/MM/YYYY') ? null : { 'date': true }
}

@Component({
  selector: 'form-race',
  templateUrl: './form-race.component.html',
  styleUrls: ['./form-race.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FormRaceComponent {
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
          key: 'date',
          className: 'col-4',
          type: 'input',
          props: {
            label: 'Fecha',
            placeholder: 'DD/MM/AAAA',
            required: true,
          },
          validators: {
            date: {
              expression: (c: AbstractControl) => moment(c.value, 'DD/MM/YYYY', true).isValid(),
              message: () => "Fecha no valida",
            },
          },
        },
        {
          key: 'edition',
          className: 'col-4',
          type: 'input',
          props: {
            type: 'number',
            label: 'Edición',
          }
        },
        {
          key: 'type',
          className: 'col-4',
          type: 'select',
          props: {
            label: 'Tipo',
            placeholder: 'Tipo de regata',
            required: true,
            options: [
              { value: 'CONVENTIONAL', label: 'Convencional' },
              { value: 'TIME_TRIAL', label: 'Contrarreloj' },
            ],
          }
        },
      ],
    },
    {
      className: 'section-label',
      template: '<hr /><div><strong>Extra:</strong></div>',
    },
    {
      fieldGroupClassName: 'row',
      fieldGroup: [
        {
          key: 'laps',
          className: 'col-6',
          type: 'input',
          props: {
            type: 'number',
            label: 'Número Largos',
            min: 1,
            max: 10,
          }
        },
        {
          key: 'lanes',
          className: 'col-6',
          type: 'input',
          props: {
            type: 'number',
            label: 'Número Calles',
            min: 1,
            max: 10,
          }
        },
      ],
    },
    {
      fieldGroupClassName: 'row',
      fieldGroup: [
        {
          key: 'organizer',
          className: 'col-6',
          type: 'input',
          props: {
            label: 'Organizador',
            placeholder: 'Organizador',
          }
        },
        {
          key: 'town',
          className: 'col-6',
          type: 'input',
          props: {
            label: 'Localidad',
            placeholder: 'Localidad',
          }
        },
      ],
    },
  ];

  onSubmit(model: FormModel) {
    this.onRequest.emit({
      model: "RACE",
      type: "CREATE",
      changes: Object.entries(model).map(([key, value]) => ({ key, value })),
    });
  }
}
