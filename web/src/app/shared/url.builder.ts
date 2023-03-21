import { PaginationConfig } from "src/types";

export class URLBuilder {

  private readonly _host: string;
  private _path = '';

  private _urlParams: { [name: string]: string | number | null } = {};
  private _queryParams: { [name: string]: string | number } = {};

  private _firstQueryInvoked = false;
  private _parameterMatcher = /(:\b\D\w*)/g;

  public static toFileObject(dataURI: string): File {
    // separate out the mime component
    const mimeString = dataURI.split(',')[0].split(':')[1].split(';')[0];
    const byteString = atob(dataURI.split(',')[1]);

    // write the bytes of the string to an ArrayBuffer
    const ab = new ArrayBuffer(byteString.length);
    const ia = new Uint8Array(ab);
    for (let i = 0; i < byteString.length; i++) {
      ia[i] = byteString.charCodeAt(i);
    }

    // write the ArrayBuffer to a blob, and you're done
    const blob = new Blob([ab], { type: mimeString });
    return (blob as File);
  }

  constructor(host: string) {
    if (!host.endsWith('/')) {
      throw new Error('Host url should end with \'/\'');
    }
    this._host = host;
  }

  private _extractUrlParams(url: string) {
    const parameters = url.match(this._parameterMatcher);
    if (parameters) {
      parameters.forEach(value => this._urlParams[value] = null);
    }
  }

  private _substituteParams(url: string): string {
    let substitutedUrl = url;
    Object.keys(this._urlParams).forEach(key => {
      const value = this._urlParams[key];
      if (!value) {
        throw new Error(`The parameter ${key} has not been set`);
      }
      substitutedUrl = substitutedUrl.replace(key, String(value));
    });
    return substitutedUrl;
  }

  private _substituteQueryParams(url: string) {
    let substitutedUrl = url;
    this._firstQueryInvoked = false;
    Object.keys(this._queryParams).forEach(key => {
      const value = this._queryParams[key];
      if (!this._firstQueryInvoked) {
        this._firstQueryInvoked = true;
        substitutedUrl = `${substitutedUrl}?${key}=${value}`;
      } else {
        substitutedUrl = `${substitutedUrl}&${key}=${value}`;
      }
    });
    return substitutedUrl;
  }

  public path(url: string): URLBuilder {
    this._path = url;
    if (this._path.startsWith('/')) {
      this._path = this._path.slice(1);
    }
    this._extractUrlParams(this._path);
    return this;
  }

  public setParam(paramName: string, value: string): URLBuilder {
    this._urlParams[`:${paramName}`] = value;
    return this;
  }

  public addQueryParam(paramName: string, value: string): URLBuilder {
    this._queryParams[paramName] = value;
    return this;
  }

  public setPage(page: PaginationConfig): URLBuilder {
    this.addQueryParam('limit', `${page.itemsPerPage}`);
    this.addQueryParam('offset', `${(page.page - 1) * page.itemsPerPage}`);
    if (page.sortBy) this.addQueryParam('ordering', page.sortBy)
    return this
  }

  public setFilters(filters: object): URLBuilder {
    Object.entries(filters)
      .forEach(([key, value]) => this.addQueryParam(key, value ? `${value}` : ''));
    return this
  }

  public build(): string {
    return this._substituteQueryParams(this._substituteParams(`${this._host}${this._path}`));
  }

}
