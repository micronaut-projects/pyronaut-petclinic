# Pyronaut PetClinic

This repository is a Pyronaut port of the Micronaut PetClinic sample application. It demonstrates how to build a Python application on Micronaut using Pyronaut, Micronaut Data JDBC, Micronaut Views, validation, test resources, and an Oracle database.

## What This Sample Shows

- Python controllers, entities, repositories, and services running in a Micronaut application.
- Micronaut Data JDBC repositories backed by Oracle.
- Micronaut validation annotations on Python form objects.
- Micronaut `@Mapper` usage for form-to-entity mapping.
- Server-side HTML rendering through Micronaut Views Jinjava templates.
- Static resources served from the `static/` resource directory.
- Oracle Test Resources provisioning for local tests and development runs.
- Pytest integration through `micronaut-pyronaut-pytest`.
- The Micronaut Control Panel in development mode.

## Requirements

- A recent Pyronaut SDK installed from the matching Pyronaut development branch.
- Docker or a compatible container runtime for Oracle Test Resources.
- Java/GraalVM requirements as expected by the installed Pyronaut SDK.

The project is configured for the JVM Pyronaut toolchain:

```toml
[tool.pyronaut.toolchain]
type = 'jvm'
```

## Project Layout

```text
config/          Micronaut application configuration
src/             Python application code
static/          Static web assets
tests/           Pytest test suite
tests-config/    Test-specific Micronaut configuration
views/           HTML template files
```

Generated files are written under `__pyronaut__/` and local Test Resources state is written under `.micronaut/`. Both directories are intentionally ignored by Git.

## Install Dependencies

From the repository root:

```bash
pyronaut install
```

This resolves runtime, build, test, and development dependencies into the local Pyronaut cache directory.

## Run

```bash
pyronaut dev
```

The application starts on the default Micronaut port, usually `http://localhost:8080`.

Useful routes:

- `http://localhost:8080/`
- `http://localhost:8080/owners/find`
- `http://localhost:8080/vets`
- `http://localhost:8080/vets/json`
- `http://localhost:8080/control-panel`
- `http://localhost:8080/health`

## Test

```bash
pyronaut test
```

The tests start the application with Oracle supplied by Micronaut Test Resources. The suite covers seed data, owners, pets, visits, vets, JSON output, form flows, not-found behavior, and template rendering.

## Database

Oracle is the only configured database dialect for this sample. The application omits fixed datasource URLs and credentials so Micronaut Test Resources can provide them during local runs and tests.

Relevant configuration lives in `config/application.toml` and `tests-config/application-test.toml`.

## Template Rendering

Micronaut controllers use `@View` and the Micronaut Views Jinjava renderer. Templates live in `views/`, use the `.jinja` extension, and compose pages with Jinja inheritance and includes. Dynamic values are escaped by the templates using Jinjava's HTML escaping filters.
