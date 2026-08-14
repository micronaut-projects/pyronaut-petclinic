# Pyronaut PetClinic

This PetClinic implementation is a Python JSON API plus a React 18 single-page application.
Micronaut Views React server-renders the initial document, and the browser hydrates the same route
tree. In Pyronaut, React rendering leases the Python-owned polyglot contexts, so GraalPy and
GraalJS run in one VM without a separate React engine or context pool.

The application keeps the familiar browser URLs (`/owners/find`, `/owners/{id}`, `/vets`, and the
pet/visit form URLs). Data operations use `/api/**`; `/vets/json` remains as a compatibility alias.

## Project Layout

```text
config/           Micronaut application configuration
frontend/         Shared React route tree plus client and server entry points
src/              Python controllers, entities, repositories, forms, and services
static/           CSS, images, and the generated browser hydration bundle
tests/            Pytest integration tests
tests-config/     Test-specific Micronaut configuration
views/            Generated React server-rendering bundle
```

Generated JavaScript bundles, Pyronaut files under `__pyronaut__/`, local Test Resources state
under `.micronaut/`, and `node_modules/` are intentionally ignored by Git.

## Requirements

- A Pyronaut SDK containing `micronaut-pyronaut-views-react`
- GraalPy 25.x and GraalJS Community (selected in `pyproject.toml`)
- Node.js and npm
- Docker or another Test Resources-compatible container runtime for Oracle

## Build and test

```bash
npm ci
npm test
npm run build
pyronaut install
pyronaut test
```

The JavaScript bundles are generated and intentionally not committed. `npm run build` writes the
server bundle to `views/ssr-components.mjs` and the hydration bundle to `static/client.js`.

For development, run the JavaScript watcher and Pyronaut development server in separate terminals:

```bash
npm run watch
pyronaut dev
```

Static assets are served from `/static/**`. React Views uses
`classpath:views/ssr-components.mjs` for SSR and `/static/client.js` for hydration.

## HTTP API

- `GET|POST /api/owners`
- `GET|PUT /api/owners/{ownerId}`
- `GET /api/pet-types`
- `POST /api/owners/{ownerId}/pets`
- `GET|PUT /api/owners/{ownerId}/pets/{petId}`
- `POST /api/owners/{ownerId}/pets/{petId}/visits`
- `GET /api/vets`

Validation failures return HTTP 422 with `{message, errors}`. Nested pet and visit routes validate
that the resource belongs to the owner named in the URL.
