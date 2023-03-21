import { ChangeDetectionStrategy, Component, EventEmitter, Input, OnDestroy, OnInit, Output } from '@angular/core';
import { debounceTime, distinctUntilChanged, ReplaySubject, takeWhile } from "rxjs";
import { NG_IF } from "src/app/shared/animations";


@Component({
  selector: 'search',
  templateUrl: './search-bar.component.html',
  styleUrls: ['./search-bar.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  animations: [...NG_IF],
})
export class SearchBarComponent implements OnInit, OnDestroy {
  private activeComponent: boolean = false;
  @Input() badges: string[] = [];

  @Output() onKeywordsChanged = new EventEmitter<string>();

  keywords: string = '';
  searching = new ReplaySubject<string>();
  showContent: boolean = false

  get windowsWidth() {
    return window.innerWidth
  }

  ngOnInit() {
    this.activeComponent = true;

    // subscribe to searchin behaviour
    this.searching.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      takeWhile(() => this.activeComponent),
    ).subscribe(keywords => {
      return this.onKeywordsChanged.emit(keywords);
    });
  }

  ngOnDestroy() {
    this.activeComponent = false;
  }

  toggleContent() {
    this.showContent = !this.showContent;
  }

  clearKeywords() {
    this.keywords = '';
    this.changeKeywords();
  }

  changeKeywords() {
    this.searching.next(this.keywords);
  }
}
