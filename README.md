# Pyronaut PetClinic

This repository is a Pyronaut port of the Micronaut PetClinic sample application. It demonstrates Python on Micronaut with generated JDBC repositories, views, validation, caching and H2, Oracle, PostgreSQL or MySQL databases.

The [porting issue log](docs/porting-issues.md) records encountered problems, reproduction steps, workarounds, and issue candidates to file later.

## What This Sample Shows

- Python controllers, entities, repositories, and services running in a Micronaut application.
- Dialect-selected Micronaut Data JDBC repositories for H2, Oracle, PostgreSQL and MySQL.
- Spatial clinic searches on all four databases: radius, polygon containment, service-area intersection, and Boolean availability filters.
- Clinic-specific service catalogs with generated composite-key `@Upsert` and exact decimal prices.
- Visit duration and follow-up intervals with inclusive database search filters.
- Generated veterinarian row ETags with `If-Match` updates/deletes and transactional speciality assignments.
- Veterinarian and speciality JSON CRUD, create/edit forms and structured exception responses.
- Caffeine caching on `ClinicService.find_all_vets`; the newer CRUD service reads fresh state.
- Oracle vector retrieval using the reference's static 384-dimensional embedding catalog.
- Owner care JSON duality documents with nested updates and Oracle ETAG conflict handling.
- Oracle priority transactions where an emergency HIGH booking displaces a regular LOW booking.
- English, Spanish and German message bundles with persistent locale selection.
- Micronaut validation annotations on Python form objects.
- Micronaut `@Mapper` usage for form-to-entity mapping.
- Server-side HTML rendering through Micronaut Views Jinjava templates.
- Static resources served from the `static/` resource directory.
- External database Test Resources provisioning for local tests and development runs.
- Pytest integration through `micronaut-pyronaut-pytest`.
- The Micronaut Control Panel in development mode.

## Requirements

- Pyronaut SDK installed and on `PATH`. The current application was verified with SDK `0.1.1`.
- Docker or a compatible container runtime for external database Test Resources; H2 runs in memory.
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
src-java/        H2 ETag adapter, datasource bootstrap and Oracle priority session cleanup
static/          Static web assets
tests/           Pytest test suite
tests-config/    Test-specific Micronaut configuration
views/           HTML template files
```

Generated files are written under `__pyronaut__/` and local Test Resources state is written under `.micronaut/`. Both directories are intentionally ignored by Git.

Application layers under `src/petclinic/` are split into packages:

| Package | Contents |
| --- | --- |
| `repositories/` | Contracts and dialect implementations grouped by owners, pets, visits, vets, clinics, appointments, care records and knowledge |
| `services/` | Shared clinic facade, feature services, embeddings, startup loading and presentation helpers |
| `controllers/` | Routes grouped by functionality, shared form helpers and global error handlers |
| `models/` | Domain entities, appointment enums, persistence projections and Oracle document/vector models |
| `dtos/` | Owner/pet/visit forms, veterinarian forms, clinic requests/responses and booking/search response objects |

These are Python namespace packages: Pyronaut generates their runtime `__init__.py` files. Import a class from its owning module, such as `petclinic.models.patients`, `petclinic.dtos.vets`, `petclinic.repositories.owners` or `petclinic.services.vets`. Related owner/pet/visit models stay together so their bidirectional relationships do not introduce circular imports.

Concrete dialect repositories retain their explicit CRUD/query declarations because the inherited generic and dialect metadata paths still need framework workarounds (PORT-035/039).

## Install Dependencies

Provision the installed SDK once, then install the project dependencies from the repository root:

```bash
pyronaut setup
pyronaut install
```

`pyronaut install` resolves JVM dependencies and creates a matching GraalPy `.venv` with pytest when no project environment exists. An existing environment must be compatible with the installed SDK.

## Run

```bash
pyronaut dev
```

The application starts with H2 on the default Micronaut port, usually `http://localhost:8080`. Select another database with `MICRONAUT_ENVIRONMENTS=oracle`, `postgres` or `mysql`, for example:

```bash
MICRONAUT_ENVIRONMENTS=oracle pyronaut dev
```

Shared `application.toml` contains no datasource settings. H2 connection and migration settings live in `application-h2.toml`; a small Micronaut context configurer loads that fallback only when no datasource dialect is configured, including ordinary `dev` and `test` startup. Explicit database profiles load their own configuration without inheriting H2 values. Test Resources resolves external connection details; an existing server can be configured through `DATASOURCES_DEFAULT_URL`, `DATASOURCES_DEFAULT_USERNAME` and `DATASOURCES_DEFAULT_PASSWORD`.

`pyronaut dev` starts Test Resources for development. `pyronaut run` launches the processed application without starting Test Resources; external database profiles need an existing database and its connection settings. The default H2 configuration remains in memory. `pyronaut run dev` passes `dev` as an application argument rather than selecting development mode.

The visits search, knowledge, priority and care-record routes below are enabled when `datasources.default.dialect` is `ORACLE`, normally selected through the `oracle` profile. Ordinary visit creation and history are shared by all profiles.

Useful routes:

- `http://localhost:8080/`
- `http://localhost:8080/owners/find`
- `http://localhost:8080/vets`
- `http://localhost:8080/vets/json`
- `http://localhost:8080/vets/new`
- `http://localhost:8080/vets/specialities`
- `http://localhost:8080/clinics`
- `http://localhost:8080/visits` — Oracle only
- `http://localhost:8080/knowledge` — Oracle only
- `http://localhost:8080/oracle/transaction-priority` — Oracle only
- `http://localhost:8080/owners/1/care-record` — Oracle only
- `http://localhost:8080/control-panel` — development mode
- `http://localhost:8080/health`
- `http://localhost:8080/info`

## Test

```bash
pyronaut test
```

The default test invocation selects Oracle and runs shared and Oracle-specific checks, skipping the H2-only connection regression. Select another database profile with `PETCLINIC_TEST_DATABASE`:

```bash
PETCLINIC_TEST_DATABASE=h2 pyronaut test
PETCLINIC_TEST_DATABASE=postgres pyronaut test
PETCLINIC_TEST_DATABASE=mysql pyronaut test
```

Tests are split by functionality under `tests/`, with shared fixtures in `conftest.py`. Shared cases cover core workflows, current vet/speciality CRUD and ETags, Unicode boundaries, JSON/HTML errors, health/info, spatial queries and geometry writes, catalogs, localization, resources and cache behavior. Oracle adds interval comparisons, vector ranking/thresholds, duality updates and competing priority transactions. Oracle-only cases declare their requirement at the module level; the H2GIS connection regression runs only on H2. See the [test guide](tests/README.md).

These commands run SDK configuration validation. A single documented suppression covers the SDK schema's incorrect shape for Oracle Test Resources file-copy settings; actual container initialization is verified by the Oracle tests.

Use a GraalPy environment matching the installed Pyronaut SDK for pytest. An ordinary CPython `.venv` is not compatible with the embedded Python test runner.

## Database

H2 is the default in-memory database, matching the reference. All profiles use Hikari. Each dialect selects its repository beans; profiles provide the matching connection and migration settings; existing Oracle migration history remains intact.

| Environment | Configuration | Development/test database |
| --- | --- | --- |
| Default / `h2` | `config/application-h2.toml` | In-memory H2 with H2GIS |
| `oracle` | `config/application-oracle.toml` | `gvenzl/oracle-free:23.26.2-faststart` |
| `postgres` | `config/application-postgres.toml` | `postgis/postgis:18-3.6-alpine` |
| `mysql` | `config/application-mysql.toml` | `mysql:8.4.5` |

Test Resources supplies external datasource URLs and credentials during development/tests. External profiles contain no hardcoded connection URL or localhost fallback. For an existing database, provide `DATASOURCES_DEFAULT_URL`, `DATASOURCES_DEFAULT_USERNAME` and `DATASOURCES_DEFAULT_PASSWORD`.

MySQL Test Resources enables creation of the deterministic ETag routine in its local container. Existing MySQL servers require appropriate routine provisioning/settings. PostgreSQL has a computed-column workaround for generated ETag identifier quoting; details are recorded in the issue log. Original migration files are preserved, with schema and fixture corrections applied through new versions.

The regular Oracle image includes spatial types; the slim image cannot run that feature. PostgreSQL uses PostGIS for the same spatial operations. CI runs the four database profiles through `pyronaut test`; Test Resources/Testcontainers provisions and cleans up the databases using the image settings in each profile. H2 runs in memory. Local verification uses the existing cached images.

The migrations provide visit intervals, 20 clinic branches, 62 service offerings and appointment fixtures. Oracle additionally has native interval/vector storage and the owner-care duality view; its startup loader reads the reference's 10 knowledge documents and 20 chunks. Fixture lifecycle differences and remaining parity checks are tracked in the issue log.

Run SDK commands from the project root so Test Resources can copy the Oracle priority setup script from `config/oracle/01-priority.sql`. The booking pause defaults to 15 seconds, matching the reference. LOW demo transactions retire their physical connection after cleanup to avoid a reproduced Oracle/JDBC session-reuse failure; the repeated-booking regression and workaround are documented as PORT-054 in the issue log.

The clinic map loads Leaflet and drawing controls from a CDN. Coordinate-based search remains available when those assets cannot load.

## Template Rendering

Micronaut controllers use `@View` and the Micronaut Views Jinjava renderer. Templates live in `views/`, use the `.jinja` extension, and compose pages with Jinja inheritance and includes. Dynamic values are escaped by the templates using Jinjava's HTML escaping filters.

## License

Apache License 2.0.
