import { Component, OnDestroy, OnInit } from '@angular/core';
import { BehaviorSubject, filter, map, takeWhile, tap } from "rxjs";
import { ActivatedRoute, Router } from "@angular/router";

interface QueryParams {
  type?: string;
}

@Component({
  selector: 'requests',
  templateUrl: './requests.component.html',
  styleUrls: ['./requests.component.scss']
})
export class RequestsComponent implements OnInit, OnDestroy {
  private activeComponent = false;
  params$: BehaviorSubject<QueryParams> = new BehaviorSubject({});

  constructor(private _route: ActivatedRoute, private _router: Router) {
  }

  ngOnInit() {
    this.activeComponent = true;

    this._route.queryParams.pipe(
      tap(params => !params['type']
        ? this._router.navigate(['requests'], { queryParams: { type: 'races' } })
        : params),
      filter(params => !!params['type']),
      map(params => params['type']),
      takeWhile(() => this.activeComponent),
    ).subscribe(
      type => this.params$.next({ type })
    )
  }

  ngOnDestroy() {
    this.activeComponent = false;
  }
}
