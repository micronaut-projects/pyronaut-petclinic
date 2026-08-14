import 'web-streams-polyfill/dist/polyfill';

// GraalJS does not expose the browser URL globals used by React Router during SSR.
// Keep this small WHATWG-compatible subset local to the server bundle; the browser
// bundle uses the platform implementations.
if (!globalThis.URLSearchParams) {
  globalThis.URLSearchParams = class {
    constructor(value = '') {
      this.values = new Map();
      const query = String(value).replace(/^\?/, '');
      if (query) {
        for (const pair of query.split('&')) {
          const [key, val = ''] = pair.split('=');
          this.append(decodeURIComponent(key), decodeURIComponent(val));
        }
      }
    }
    append(key, value) {
      const values = this.values.get(String(key)) || [];
      values.push(String(value));
      this.values.set(String(key), values);
    }
    get(key) {
      const values = this.values.get(String(key));
      return values && values.length ? values[0] : null;
    }
    getAll(key) {
      return [...(this.values.get(String(key)) || [])];
    }
    delete(key) {
      this.values.delete(String(key));
    }
    toString() {
      return [...this.values].flatMap(([key, values]) => values.map(value =>
        `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)).join('&');
    }
  };
}
if (!globalThis.URL) {
  globalThis.URL = class {
    constructor(value, base = 'http://localhost') {
      let text = String(value);
      if (!/^[a-z][a-z0-9+.-]*:\/\//i.test(text)) {
        text = `${String(base).replace(/\/$/, '')}/${text.replace(/^\//, '')}`;
      }
      const match = text.match(/^([^:]+:\/\/[^/]+)(\/[^?#]*)?(\?[^#]*)?(#.*)?$/);
      this.origin = match ? match[1] : '';
      this.pathname = (match && match[2]) || '/';
      this.search = (match && match[3]) || '';
      this.hash = (match && match[4]) || '';
      this.href = `${this.origin}${this.pathname}${this.search}${this.hash}`;
      this.searchParams = new globalThis.URLSearchParams(this.search);
    }
  };
}
import React from 'react';
import * as ReactDOMServer from 'react-dom/server.browser';
import {App} from './src/App';

export {App, React, ReactDOMServer};
