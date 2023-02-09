import { platformBrowserDynamic } from '@angular/platform-browser-dynamic';

import { AppModule } from './app/app.module';

import * as dayjs from "dayjs";
import * as customParseFormat from "dayjs/plugin/customParseFormat";
import * as duration from "dayjs/plugin/duration";
import "dayjs/locale/es";

dayjs.extend(customParseFormat)
dayjs.extend(duration)
dayjs.locale("es")

platformBrowserDynamic().bootstrapModule(AppModule)
  .catch(err => console.error(err));
