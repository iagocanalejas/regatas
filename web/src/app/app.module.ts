import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppComponent } from './app.component';
import { StoreModule } from '@ngrx/store';
import { metaReducers, reducers } from './reducers';
import { EffectsModule } from '@ngrx/effects';
import { StoreRouterConnectingModule } from '@ngrx/router-store';
import { StoreDevtoolsModule } from '@ngrx/store-devtools';
import { environment } from '../environments/environment';
import { AppService } from "./app.service";
import { AppEffects } from "./reducers/app.effects";
import { HttpClientModule } from "@angular/common/http";
import { RoutingModule } from "./app.routes";
import { BrowserAnimationsModule } from "@angular/platform-browser/animations";
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { LoadingBarModule } from "@ngx-loading-bar/core";
import { LoadingBarHttpClientModule } from "@ngx-loading-bar/http-client";

const runtimeChecks = {
  // strictStateImmutability and strictActionImmutability are enabled by default
  strictStateSerializability: !environment.production,
  strictActionSerializability: !environment.production,
  strictActionWithinNgZone: !environment.production,
  strictActionTypeUniqueness: !environment.production,
}

@NgModule({
  declarations: [
    AppComponent
  ],
  imports: [
    BrowserModule, BrowserAnimationsModule, HttpClientModule, RoutingModule, NgbModule,
    LoadingBarHttpClientModule, LoadingBarModule,
    StoreModule.forRoot(reducers, { metaReducers, runtimeChecks }),
    EffectsModule.forRoot([AppEffects]),
    StoreRouterConnectingModule.forRoot(),
    StoreDevtoolsModule.instrument({ maxAge: 25, logOnly: environment.production }),
  ],
  providers: [AppService],
  bootstrap: [AppComponent]
})
export class AppModule {
}
