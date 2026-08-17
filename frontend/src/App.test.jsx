import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server.node';
import {App} from './App';

test('renders server-provided veterinarians', () => {
  const html = renderToStaticMarkup(<App page="vets" data={{vets: [{
    id: 1, firstName: 'James', lastName: 'Carter', specialitiesAsString: 'none'
  }]}} url="/vets"/>);
  expect(html).toContain('James Carter');
});

test('renders a server-provided not-found page', () => {
  const html = renderToStaticMarkup(
    <App page="notFound" data={{message: 'Owner not found'}} url="/missing"/>
  );
  expect(html).toContain('Owner not found');
});
