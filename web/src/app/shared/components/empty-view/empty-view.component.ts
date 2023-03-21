import {ChangeDetectionStrategy, Component, Input, OnInit} from '@angular/core';

@Component({
  selector: 'no-content',
  templateUrl: './empty-view.component.html',
  styleUrls: ['./empty-view.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class EmptyViewComponent implements OnInit {

  @Input() text!: string;
  @Input() materialIcon: string = 'report';
  @Input() topMargin: object = {'margin-top': '0'};

  public ngOnInit() {
    if (!this.text) {
      this.text = 'Sin resultados';
      this.topMargin = {'margin-top': '20%'};
    }
  }

}
