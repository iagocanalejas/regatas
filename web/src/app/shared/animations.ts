import {animate, state, style, transition, trigger} from '@angular/animations';

export const ROTATE = [
  trigger('rotateAnimation', [
    state('0', style({})),
    state('1', style({
      transform: 'rotate(90deg)'
    })),
    transition('0 => 1', animate('200ms ease-in')),
    transition('1 => 0', animate('200ms ease-out'))
  ]),
];
export const NG_IF = [
  trigger(
    'showAnimation', [
      transition(':enter', [
        style({height: 0, opacity: 0}),
        animate('200ms ease-in', style({height: '*', opacity: 1}))
      ]),
      transition(':leave', [
        style({height: '*', opacity: 1}),
        animate('200ms ease-out', style({height: 0, opacity: 0}))
      ])
    ]
  )
];
