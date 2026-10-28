# PetClinic port: open issues and retained workarounds

Updated: 2026-10-28 (ownership triage and SDK follow-up). Scope: a faithful Micronaut PetClinic port to Pyronaut.

This is a working log for filing issues later. No external issues have been created. It retains open issues, framework improvements, unresolved investigations and active workarounds. Local environment/provisioning issues and fully resolved entries needing no workaround are excluded. A reproduction specific to this SDK is not a claim that all Pyronaut versions are affected.

**Latest scope:** check the updated local Java reference, organize repositories/services/controllers/models/DTOs by functionality, verify SDK 0.1.1 compatibility, isolate datasource profiles, and select database beans by datasource dialect. The earlier stabilization backlog remains deferred except for the corrections recorded below.

## Reproduction versions and configuration

The original findings used the versions below. The latest checkpoint records the SDK 0.1.1 verification separately.

- Pyronaut SDK `0.0.3`; Micronaut Core `5.2.2`; SDK platform `5.1.0`.
- Micronaut Data runtime/processor `5.2.3`; Micronaut Serialization `3.1.0`.
- Embedded GraalPy `25.3.4.1`; matching GraalPy 3.13 used for pytest.
- Cached Oracle image `gvenzl/oracle-free:23.26.2-faststart`.
- Early checks used `pyronaut test --no-validate`. The final 2026-10-27 matrix enabled configuration validation with one narrow suppression for `test-resources.containers.oracle.copy-to-container`; see PORT-027.

Record a reduced reproduction and reconfirm it before opening an upstream issue. An active workaround or documentation gap alone does not establish a framework defect.

## Ownership triage (2026-10-28)

All **30 retained entries** are classified below. Original issue identifiers are preserved, so numbering has gaps after removing environment-only findings and fully resolved entries that need no workaround. The original ownership triage reviewed saved sources/artifacts; the SDK 0.1.1 findings below come from the subsequent regression check. No external issues have been filed. Historical details describe the code at the time of each failure; a working workaround does not establish that its underlying framework limitation has been fixed.

| Primary classification | Entries | Meaning |
| --- | ---: | --- |
| Framework candidate | 14 | Observed behavior warrants an upstream defect investigation; package ownership still needs a reduced reproduction |
| Framework improvement | 5 | Interop documentation, diagnostics or capability configuration; no correctness defect established |
| Application/test | 3 | Open application work or implementation choices still needing verification/workarounds |
| Reference application | 3 | Java sample behavior or schema; not automatically a Pyronaut issue |
| Unresolved | 5 | Evidence has not yet isolated the responsible resource, library or runtime |

Counts assign each PORT identifier once. Mixed entries have separately named parts below; their secondary improvement opportunities are not additional bugs. Of the 14 framework candidates, **13 should initially be investigated through the Pyronaut integration and one (PORT-046) through Micronaut Data**. This is a routing recommendation, not a claim of 13 proven Pyronaut defects.

### Complete disposition

| Finding | Primary classification | Owner, reasoning and disposition |
| --- | --- | --- |
| PORT-001 | Framework candidate | **Pyronaut script/executor integration.** Explicit blocking execution hangs script routes, while class controllers work. Retain the class-controller workaround; reduce scheduling before assigning the underlying runtime cause. |
| PORT-004 | Unresolved | **Resource discovery and caller-sensitive Java invocation are separate failures.** `Environment` loading works. Isolate packaging/classloader selection from restricted MethodHandle access before routing to Pyronaut, GraalPy or application configuration. |
| PORT-009 | Framework improvement | **Interop documentation.** Java duration conversion to `timedelta` requires application normalization; no stored-value loss was demonstrated. Document the supported representation. |
| PORT-010 | Unresolved | **Period conversion/comparison.** Normalization fixes the bound, but the cause could be application expectations, Data conversion or the Oracle driver. Compare all three before filing. |
| PORT-011 | Application/test | **Our upsert response design.** Re-read the persisted natural key instead of assuming the candidate sequence ID. The entry records a precaution, not a captured wrong-ID defect. Concurrent first insertion remains an application verification task. |
| PORT-015 | Framework improvement | **Validation-path interop API/documentation.** An iterable path becomes a node list, so stringifying it is unsuitable. Document node traversal or offer a path formatter; no validation-engine defect established. |
| PORT-016 | Framework candidate | **Pyronaut AST / Data metadata integration.** `findField` cannot see a declared Python entity field. Explicit column mappings work; reduce field exposure rather than treating every JSON-view error as application mapping. |
| PORT-017 | Unresolved | **Oracle JSON / LocalDate compatibility.** The time-bearing Oracle value fails the date-only deserializer. An explicit format fixes it, but the Java/Python behavior under identical mappings has not been isolated; do not assign it to Pyronaut yet. |
| PORT-018 | Framework candidate | **Pyronaut type-use metadata / Validation (018b).** Element-level `@Valid` did not cascade on SDK 0.0.3 and generates invalid Java constructor annotations on 0.1.1. Omit the unsupported collection annotations and retain manual traversal. |
| PORT-020 | Framework candidate | **Pyronaut annotation-binding generation.** A generated binding imports an ungenerated transitive annotation module. Explicitly importing both annotations is a workaround, not a normal missing application dependency. |
| PORT-021 | Framework improvement | **Repository-return interop documentation.** Java mirrors are not Python dataclasses; `dataclasses.replace` is inapplicable. Document construction/enum normalization; native-dataclass ergonomics are a separate enhancement. |
| PORT-022 | Framework candidate | **Pyronaut HTTP enum conversion.** Lowercase reference inputs fail generated binding. String conversion works. Confirm enum converter registration and Java/Python equivalence before choosing Pyronaut versus Core ownership. |
| PORT-024 | Framework improvement | **Embedded runtime capability/configuration.** Python threads are disabled in this context. Document or expose supported configuration if available; this is not evidence that HTTP requests cannot overlap. Java async priority checks do overlap. |
| PORT-026 | Framework improvement | **Foreign-exception documentation.** Explicit Java exception catches work where Python `Exception` does not. Document the hierarchy; the expected ORA-00054 lock result is not a persistence failure. |
| PORT-027 | Framework candidate | **Configuration schema mismatch (027b).** The SDK schema rejects the working runtime list-of-maps shape. Retain the narrow validation suppression and investigate schema generation/config metadata ownership. |
| PORT-028 | Application/test | **Separate-process resource configuration.** The Test Resources server does not automatically share the application's classpath. Host-path copying works. SDK resource resolution/docs could improve; no promised application-classpath visibility is established. |
| PORT-031 | Reference application | **Source ownership policy.** Cross-owner paths/reassignment are reference behavior. Preserve the requested parity; any stricter policy is a separate product/reference decision, not a Pyronaut fix. |
| PORT-032 | Reference application | **Source error handlers/rendering.** Wrong parameter lookup and creation/edit context are Java sample defects. Reconfirm against the current reference before filing; unsupported content-type status behavior may require a separate Core reproduction. |
| PORT-035 | Framework candidate | **Pyronaut generic bridge generation.** Nested repository inheritance emits signatures that clash or fail to override. The Java structure compiles; retain the verified direct-CRUD workaround and reduce generated signatures. |
| PORT-038 | Reference application | **Source decimal DDL.** Scale-zero H2 `DECIMAL` loses fractions as declared. The reference schema/mapping needs a fix; ours explicitly preserves scale. A Data schema-generation claim needs an annotation-contract reproduction first. |
| PORT-039 | Framework candidate | **Pyronaut AST / Data query specialization.** Inherited queries execute SQL from another dialect despite correct bean selection. Redeclarations fix all profiles. Reduce owning-type metadata; not a missing spatial extension. |
| PORT-040 | Framework candidate | **Pyronaut test reporting.** SDK 0.1.1 still reports zero suite-level skips despite skipped child cases. Count the children; skipped features are not passed features. |
| PORT-042 | Application/test | **Open application lifecycle gap.** Core SQL seeds ignore `petclinic.sample-data.enabled=false`. Separate conditional fixtures safely from schema migration history; the framework already supports conditional beans. |
| PORT-043 | Unresolved | **Removed fixture experiment.** Its resource lookup failure is historical and not reproducible from the current tree. First establish processed-resource presence and context configuration; no upstream owner assigned. |
| PORT-045 | Framework candidate | **Mixed:** nullable typed IDs becoming zero (**045a**) warrant a binding/serialization defect investigation; `ForeignNone` identity in object collections (**045b**) is an interop adaptation. Reject malformed inputs before deduplication in our code. |
| PORT-046 | Framework candidate | **Micronaut Data ETag SQL generation.** Unquoted mapped identifiers break PostgreSQL. Generated lowercase aliases are our workaround; prove the Java control before describing this as Pyronaut-specific. PostgreSQL identifier folding is expected. |
| PORT-051 | Framework candidate | **Embedded pytest capture on SDK 0.1.1.** Default file-descriptor capture aborts pytest before cases run. Python stream capture permits execution; retain `--capture=sys` in pytest configuration and reduce the runner/filesystem interaction. |
| PORT-052 | Framework candidate | **Python exception mirrors across service boundaries.** An already-taken booking becomes a Java exception mirror; checking the Python exception type raises an interop attribute error. Detect its generated Java type first while preserving the HTTP 409 outcome. |
| PORT-053 | Framework candidate | **Pyronaut pytest application-configurer discovery.** The fixture builder selects its application classloader after the base builder has loaded configurers. A project `@ContextConfigurer` is missed; explicitly select the H2 test profile and exercise default startup through an application-classloader builder. |
| PORT-054 | Unresolved | **Oracle database/JDBC priority-session reuse.** Plain JDBC reproduces a first correct rollback followed by LOW silently overwriting committed HIGH bookings on a reused session. This is outside Pyronaut/Micronaut; distinguish the database from its JDBC driver before filing. Retire LOW demo connections after cleanup and verify repeated races. |

### Framework defect investigation queue

Priorities below reflect potential impact without our workarounds, not current failures in the stabilized port. **Strong evidence** means a concrete failing artifact, source mechanism or controlled workaround is recorded; it does not establish the responsible package or a defect in the latest release. **Tentative evidence** needs a tighter behavioral control before filing.

| Order | Candidate and likely first owner | Evidence / impact | Smallest useful reproduction and acceptance condition |
| ---: | --- | --- | --- |
| 1 | PORT-045a — Pyronaut binding / Serialization | Strong: nullable integer elements change meaning; input integrity | One DTO with `list[int \| None]`, explicit boxed-integer variant and an echo route. Send `[null]`, `[0]`, `[1]`; inspect raw deserialized values and generated metadata. Null must remain null. Compare a Java DTO to separate Serde from the Python binding layer. |
| 2 | PORT-018b — Pyronaut type-use metadata / Validation | Strong: invalid nested data reaches Oracle | Parent with `list[Annotated[Child, Valid]]`; child with `NotBlank`. Invoke `Validator` without a database and inspect generic-argument annotations. First check that generated constructors compile without leaking internal validation annotations. Once processing succeeds, a blank child must produce an indexed violation; compare the Java equivalent. |
| 3 | PORT-035 — Pyronaut compiler | Strong: generated Java does not compile | One shared generic CRUD protocol and one dialect subclass. Attach generated signatures and javac errors beside the compiling Java equivalent. Generated methods must preserve bounds/wildcards and implement the interface. |
| 4 | PORT-039 — Pyronaut / Data metadata | Strong: wrong-dialect SQL at runtime | One inherited annotated query and two dialect implementations. Inspect each generated query independently and together. Each must retain its owning implementation's dialect; include a Java control before narrowing ownership. |
| 5 | PORT-001 — Pyronaut script execution | Tentative ownership: route hangs; class-controller control works | Same trivial route as a script and class controller, with/without `ExecuteOn`. Capture timeouts and thread/context evidence, without Oracle or priority transactions. Blocking requests must complete and independent requests must overlap. |
| 6 | PORT-016 — Pyronaut class elements / Data visitor | Strong: declared field invisible to `findField` | One Python entity with `id` and one JSON subview, without explicit `MappedProperty`. Dump property/field metadata and compare Java. Processing must see the declared field or Data must use a supported property lookup. |
| 7 | PORT-020 — Pyronaut annotation bindings | Strong: generated import targets missing module | Import only `OracleTransactional` plus the Jakarta transactional annotation. Process/start a minimal bean; inspect generated imports. Every imported stereotype binding must be present without a redundant application import. |
| 8 | PORT-046 — Micronaut Data processor | Strong: generated expression and PostgreSQL trace agree | Minimal Java and Python entities with quoted uppercase ETag input columns. Inspect `GeneratedETagUtils` output and perform one PostgreSQL read/update without aliases. Expression identifiers must follow dialect quoting while retaining generated optimistic locking. |
| 9 | PORT-027b — Pyronaut configuration schema / Test Resources metadata | Strong: working runtime shape is schema-invalid | Submit the same list-of-maps copy configuration to SDK validation and the runtime provider. Attach generated schema and provider contract. Validation must accept the supported shape without suppression; investigate whether schema generation or upstream metadata declares the wrong type. |
| 10 | PORT-040 — Pyronaut test report producer | Strong: archived XML proves skip-count inconsistency | One pass and one skip. Compare the suite's `skipped` attribute with skipped children. Counts must agree. No database needed. |
| 11 | PORT-022 — Pyronaut HTTP conversion / Core | Tentative ownership: lowercase binding fails | One enum query route, Python and Java equivalents. Compare uppercase, lowercase, missing and invalid values plus converter registration. Supported lowercase values must bind; invalid values must produce the agreed client-error response. Isolate conversion from our generic HTML handler. |
| 12 | PORT-051 — Pyronaut embedded pytest / GraalPy filesystem | Strong: unchanged suite fails before execution; stream-capture control passes | One assertion-only test under default capture and `--capture=sys`, with SDK 0.1.1 and matching GraalPy. Preserve the original exception and identify the missing capture path. The default runner must execute ordinary tests or select supported capture automatically. |
| 13 | PORT-052 — Pyronaut exception interop | Strong: real taken-booking response fails; Java-type control passes | Raise a Python custom exception from an intercepted service and catch it in a separate controller module. Compare Java/Python type checks on the received mirror. Normal exception classification must not raise a missing internal-attribute error. |
| 14 | PORT-053 — Pyronaut pytest context builder | Strong mechanism: builder bytecode and missing default datasource agree; reduced control still required | One project `@ContextConfigurer` supplying a sentinel property. Compare the pytest fixture with `ApplicationContext.builder(applicationClassLoader)`. The fixture must discover the project configurer before context configuration. |

File one issue per independently reproducible cause. PORT-035 and PORT-039 are related metadata areas but exhibit distinct compilation and query-specialization failures. Validation-path formatting (PORT-015) and repository/enum mirror handling (PORT-021) are interop improvement requests, not extra constraint or persistence bugs. PORT-027 concerns validation of the correct runtime configuration shape.

### Framework improvements worth proposing

These are enhancement/documentation requests, not additions to the defect count. Group related symptoms before filing:

- **Interop guide (PORT-009/015/021/026/045b):** duration representations, validation-node traversal, repository mirror construction, enum names, foreign null checks and catching foreign exceptions. Offer convenience APIs only where their contract is clear; document the current supported path first.
- **Runtime capability guide (PORT-024):** document Python thread restrictions and supported context options. Preserve Java async as the already verified way to exercise overlapping requests; do not imply concurrency is unsupported generally.
- **Test Resources integration (PORT-027/028):** align the configuration schema with the supported copy shape and explain server versus application classpaths. Automatic application-resource staging is an enhancement unless a supported contract promises it.

### Unresolved investigations and our remaining backlog

Do not file PORT-004, PORT-010, PORT-017, PORT-043 or PORT-054 as confirmed Pyronaut defects:

- **PORT-004:** create separate controls for resource bundle discovery, `Environment` lookup and caller-sensitive invocation. Check that the resource is packaged before blaming a classloader; route restricted Java lookup separately if reproducible without resource access.
- **PORT-010:** compare normalized/unnormalized periods through direct JDBC, Java Data and Python Data using the same stored interval. Inspect bound values and database comparisons; this determines application normalization versus library/driver ownership.
- **PORT-017:** the local Java `OwnerCareView` uses `LocalDate` without our optional-time `JsonFormat`. Compare actual Oracle JSON and Java/Python deserializers with identical versions/mappings. A formatting workaround alone does not prove a Python compiler defect.
- **PORT-043:** the failed loader experiment was removed. Reconstruct a resource-only example before revisiting seeding, inspect the processed artifact, and establish the supported fresh-context configuration. Existing `Environment` loading succeeds elsewhere; do not combine this with PORT-004 or PORT-028 without a shared cause.

- **PORT-054:** repeated raw JDBC races reproduce the session-reuse failure without framework code. Route this to Oracle database/JDBC investigation, retaining the connection-retirement workaround until corrected versions pass repeated reuse.

**PORT-042 remains the clearest open application correctness task:** the disabled sample-data flag does not suppress core SQL fixtures. Address it later through conditional loading with separate enabled/disabled/restart checks and a migration-history plan. Do not rewrite applied Oracle checksums or remove user rows. PORT-043 does not turn this application gap into a framework defect.

Other still-unverified application work is concurrent first catalog insertion (PORT-011), broader model/helper equivalence, remaining failure-contract comparisons (PORT-032), pet reassignment parity (PORT-031), packaged datasource fallback, browser behavior and remote CI. These are coverage or port-completeness tasks, not demonstrated framework bugs. Completed application corrections have been removed from this issue log; their history remains in Git.

Browser/CDN availability, packaged resources, production configuration and remote CI need their own evidence before any framework attribution.

### Evidence and filing procedure

This triage checked the current Python care-record and vet implementations, configuration suppression, local Java `OwnerCareView`, local Data `MappedEntityVisitor`/`GeneratedETagUtils`, and Test Resources `TestContainerMetadataSupport`, alongside the recorded failures. Local framework source checkouts support the investigation; establish the exact dependency/source revision in each reduced reproduction before treating them as the installed binary's implementation.

The SDK 0.1.1 H2 report at `__pyronaut__/reports/refactor-20261028/final/h2/junit.xml` has 121 child cases and 20 skipped children, but the suite attribute is still `skipped="0"`. Total-case counting and parameter identities now agree with the children, so those resolved portions are excluded from PORT-040. Generated reports remain local/ignored and must be attached explicitly when filing.

For each candidate, record the installed versions above, original failure, smallest standalone source, generated metadata/SQL or traceback, Java control where relevant, workaround and expected behavior. Reconfirm on a supported aligned toolchain and check whether the issue already exists or is fixed before filing. A single startup failure causing many test failures is one cause, not one issue per failed test. The original ownership triage changed documentation only. Subsequent application corrections and reruns are recorded in the latest checkpoint; no upstream framework code was patched.

## Detailed findings

### PORT-001 — Explicit blocking executor causes script-route HTTP timeouts

- **Area:** Pyronaut script routes / executor integration.
- **Observed:** Adding `@ExecuteOn("blocking")` to the existing HTTP script handlers allowed startup but caused the first request to time out; subsequent requests also timed out. Removing the annotation restored responses in the same application setup.
- **Reproduction:** With the current application and matching GraalPy test environment, annotate the script route handlers with `@ExecuteOn("blocking")`, process the application, and run the HTTP workflow suite.
- **Impact:** Explicitly switching these script handlers to the blocking executor is unreliable in this setup. The class-controller pattern described below supports the transaction priority feature.
- **Workaround:** Existing script handlers use the SDK's default execution path. The priority feature uses a class controller with `@ExecuteOn("blocking")`; real overlapping LOW/HIGH requests now pass with that pattern.
- **Fix needed:** Isolate a minimal reproduction, inspect script context scheduling across executor changes, and verify two independent overlapping requests and transactions. The root cause is not established.

### PORT-004 — Direct Java resource access from Python fails across class-loader boundaries

- **Area:** Python-to-Java resource access in this runtime.
- **Observed:** `ResourceBundle.getBundle("i18n.messages", locale)` could not find bundled messages. A later `Thread.currentThread().getContextClassLoader()` access failed with `IllegalAccessException: Attempt to lookup caller-sensitive method using restricted lookup object`. A default `ResourceResolver` also returned no stream for the knowledge resource.
- **Reproduction:** Call those paths from a Python bean or startup listener with the bundled message/vector files present.
- **Impact:** Straight translations of the Java resource-loading code cannot be used unchanged.
- **Workaround (verified):** Inject Micronaut `Environment` and read resources through `getResourceAsStream`. Both localized page rendering and vector loading then executed; ranked Oracle vector search passed its integration check.
- **Fix needed:** Produce separate minimal reproductions for resource discovery and caller-sensitive invocation, then document or fix the supported class-loader path. Application workaround exists; underlying runtime behavior is unresolved.

### PORT-009 — Java duration values are exposed as Python `timedelta`

- **Observed:** A loaded Java `Duration` field became `datetime.timedelta`, so calling Java `toMinutes()` directly failed.
- **Resolution:** Normalize duration display values in Python, accepting both Java `Duration` and `timedelta` representations. Persistence and interval search checks passed.
- **Issue disposition:** Interoperability behavior to document; no data loss demonstrated.

### PORT-010 — Unnormalized month periods produce surprising Oracle interval bounds

- **Observed:** A twelve-month bound built as `Period.ofMonths(12)` excluded rows stored as one year in the initial interval check.
- **Resolution:** Normalize month periods before persistence and query comparisons. Inclusive 12-month bounds and a 15-month round trip passed afterward.
- **Issue disposition:** Consider a minimal Micronaut Data/driver conversion reproduction. Application normalization is in place.

### PORT-011 — Composite upsert result needs a persisted identity lookup

- **Observed/precaution:** An upsert can allocate a candidate sequence ID even when the clinic/code conflict updates an existing row. The returned candidate must not be assumed to be the persisted row identity for every driver path.
- **Resolution:** Within the transaction, perform the generated `@Upsert`, then read by clinic/code for the response. The stable-ID and clinic-isolation checks passed.
- **Issue disposition:** Port implementation decision; a separate upstream bug is not established. Six concurrent updates of an existing offering now pass; concurrent insertion of an absent natural key remains to be checked.

### PORT-015 — Validation property paths are coerced to lists of nodes

- **Area:** GraalPy iterable coercion / Jakarta Validation integration.
- **Observed:** `str(violation.getPropertyPath())` yielded a Python list of Java node object representations. Taking its last dot-separated component generated error keys such as `ValidationPath$DefaultPropertyNode] at ...>]`, instead of `name`, `birthDate`, or `typeId`.
- **Reproduction:** Validate a Python form with empty required fields, then inspect `type(violation.getPropertyPath())` and its string representation.
- **Impact:** Stringifying the path produces unsuitable HTML/JSON field-error keys even though validation itself rejects the values. The application now traverses nodes; the remaining request is to document or simplify that API.
- **Resolution (verified):** Iterate path nodes and use `getName()` (plus container indices for nested document validation). Form field messages and nested document validation paths passed their integration checks.
- **Issue disposition:** Resolved application adaptation; framework documentation/API improvement for iterable conversion and validation-path formatting, not an established constraint-validation defect.

### PORT-016 — JSON view processing cannot find a declared Python entity field

- **Area:** Micronaut Data JSON-view validation / Python class metadata.
- **Observed:** Processing the translated owner-care subviews failed with `Json View property id doesn't exist in the defined entity class Pet`, although the Python `Pet` dataclass declares an annotated `id` field and ordinary JDBC queries use it successfully.
- **Source evidence:** `MappedEntityVisitor.validateJsonViewProperty` checks the referenced entity with `ClassElement.findField(propertyName)` and skips that check for an explicit `@MappedProperty`.
- **Impact:** The direct Java annotation translation does not process with the current SDK.
- **Workaround (verified):** Declare explicit column mappings and nested join columns on the Python JSON view classes; preserve the reference's JSON property names and update-only operations. Processing succeeds and Oracle creates the migration-managed view. Runtime reading subsequently passed with PORT-017's date-format workaround; that does not fix the original field-lookup limitation.
- **Fix needed:** Reduce to a Python entity/view reproduction and check whether Python class elements expose declared fields through the lookup used by Data. No SDK patch has been made in this repository.

### PORT-017 — Oracle date values fail owner-care JSON deserialization (workaround verified)

- **Area:** JSON duality / Oracle JSON serialization.
- **Observed:** The view migration succeeds, but GET `/owners/1/care-record` fails with `DataAccessException: Failed to read from JSON field [DATA]`. Both new duality checks fail at document retrieval; the sixteen earlier checks pass.
- **Reproduction:** Start the in-progress port with the cached Oracle image and request an existing owner's care record.
- **Impact when encountered:** The care-record editor could not load its document.
- **Confirmed cause:** Oracle emits a SQL `DATE` as `2010-09-07T00:00:00`; the current `LocalDate` deserializer rejects the time component at character 10.
- **Workaround (verified):** Use an optional time component in the nested document date format, accepting the Oracle value while retaining date-only HTTP output for a `LocalDate`. Document reads, nested saves, returned metadata and stale ETAG rejection passed against Oracle.

### PORT-018 — Nested collection cascade validation needs an explicit traversal (workaround verified)

- **Observed (PORT-018b):** With the reference's correct element annotations (`list[Annotated[PetCareSubView, Valid]]`), valid nested updates and stale ETAG handling pass, but a blank child name bypasses cascade validation and reaches Oracle, causing `ORA-42692` / `ORA-01407` and HTTP 500.
- **SDK 0.1.1 regression (2026-10-28):** Before the package refactor, the unchanged application fails processing with Core `5.2.19` / Validation `5.2.1`. Generated `PetCareSubView` and `OwnerCareView` constructors put `@ValidatedElement @RequiresValidation` on collection parameters/casts, where those annotations are not applicable. The compiler reports `annotation interface not applicable to this kind of declaration`. This is a generated-code failure, independent of database startup or the refactor.
- **Current workaround:** Omit element-level `Valid` on `pets` and `visits` and explicitly invoke Jakarta `Validator` on each child bean, prefixing its validation path with the collection index. Child field constraints and object-level metadata validation remain intact. The older manual traversal already covered valid updates, blank child fields, null child dates and metadata checks; the SDK 0.1.1 Oracle care-record cases also pass with this adaptation.
- **Evidence:** The unchanged-source compiler dump is preserved locally at `/private/tmp/pyronaut-petclinic-refactor-20261028/__pyronaut__/processor-error-dumps/pyronaut-compiler-error-20261028-124852-290.log`. Reduce constructor annotation propagation on SDK 0.1.1 separately from the older missed-cascade behavior.
- **Issue disposition:** Element-cascade integration candidate; reduce it using the correct element annotations before filing upstream. The completed annotation-placement correction is excluded from this entry.

### PORT-020 — Oracle transactional annotation binding omits its required stereotype import

- **Observed:** Adding the reference's `@OracleTransactional` processed successfully, but startup failed with `ModuleNotFoundError: No module named 'micronaut.transaction.annotation.Transactional'`.
- **Evidence:** Generated `OracleTransactional.py` imports `micronaut.transaction.annotation.Transactional`, while that generated module was absent when application code imported only Jakarta's equivalent transactional annotation.
- **Workaround (verified):** Import Micronaut's `Transactional` explicitly alongside `OracleTransactional` so both runtime annotation bindings are generated. Startup and both real LOW/HIGH transaction paths now work.
- **Issue disposition:** SDK runtime-binding generation candidate; a transitive annotation dependency should be included when its generated binding imports it.

### PORT-021 — Dataclass replacement cannot operate on repository Java mirrors

- **Observed:** Resetting appointments failed with `TypeError: replace() should be called on dataclass instances` when passing inherited repository results to `dataclasses.replace`.
- **Impact:** A direct Python translation of Java withers cannot assume every returned entity is a native Python dataclass. Enum properties may also be Java enum mirrors.
- **Resolution (verified):** Construct an `Appointment` from the returned entity's fields when replacing status, and normalize enum names at that boundary. Regular booking, reset, taken responses and emergency takeover passed with generated saves and transaction interception.
- **Issue disposition:** Port interoperability adaptation; no SDK defect is established solely by returning Java mirrors.

### PORT-022 — Lowercase booking enum query values are rejected by generated route binding

- **Observed:** `type=regular` reached an `UnsatisfiedQueryValueRouteException: Required QueryValue [type] not specified` with the generated Python enum route parameter, producing a global HTML 500. The reference's tests and UI submit lowercase `regular`/`emergency`.
- **Workaround (verified):** Bind the text query value and convert it explicitly to the same Python booking enum, accepting case-insensitive names and rejecting unknown types. Lowercase regular/emergency requests now pass; response and persisted enums remain intact.
- **Issue disposition:** Query conversion/integration candidate; reduce enum binding separately before assigning the cause upstream.

### PORT-024 — Embedded pytest cannot create Python threads

- **Observed:** The competing-booking test failed at `ThreadPoolExecutor` with `java.lang.IllegalStateException: Creating threads is not allowed`, before the second application request was exercised.
- **Impact:** A Python-thread-based test does not establish whether the application supports concurrent requests.
- **Workaround (verified):** Use Java's asynchronous HTTP client to start LOW without a Python callback, observe its actual Oracle row lock through a separate JDBC connection, then issue HIGH. The emergency commits and LOW reports the typed priority-rollback outcome.
- **Issue disposition:** Test runtime capability/configuration limitation; not evidence of an application concurrency failure by itself.

### PORT-026 — Python's broad exception clause does not catch the probe's Java SQL exception

- **Observed:** Oracle correctly signaled the held LOW row lock with `ORA-00054`, but `except Exception` did not catch the foreign `java.sql.SQLException`, aborting the concurrency test before HIGH was issued.
- **Resolution (verified):** Catch `java.sql.SQLException` explicitly in the probe and Java `RuntimeException` alongside Python `Exception` at booking/reset boundaries. The probe and real typed priority-rollback response now pass.
- **Issue disposition:** Language-boundary adaptation. The observed row-lock error is expected evidence of LOW holding the lock, not a database fault.

### PORT-027 — Configuration schema rejects the supported container-copy list shape

- **Observed (PORT-027b):** The SDK configuration schema expects an object and rejects the working runtime list-of-maps shape for `test-resources.containers.oracle.copy-to-container`.
- **Source evidence:** Test Resources 4.1.0's `extractMapFrom` accepts a list of maps; its configuration test uses a YAML list. The application's TOML array of tables (`[[test-resources.containers.oracle.copy-to-container]]`) initializes real priority takeover successfully with PORT-028's resource-copy workaround.
- **Workaround (verified):** Suppress only `test-resources.containers.oracle.copy-to-container` in `pyproject.toml`. All other configuration validation remains enabled in the final matrix.
- **Issue disposition:** Open schema/runtime contract candidate. Investigate schema generation versus Test Resources metadata so the supported runtime shape passes validation without suppression.

### PORT-028 — Test Resources server cannot load the application's startup SQL from its classpath

- **Observed:** With the supported container-copy list shape, startup failed with a `TestResourcesException` identifying the server's `AppClassLoader`. The copied SQL was specified as `classpath:oracle/01-priority.sql`; application resources are not exposed through that server classloader in this CLI setup.
- **Workaround (verified):** Copy `config/oracle/01-priority.sql` using a host path when running the SDK from the project root. Both priority HTTP checks pass with automatic setup and no diagnostic override. The script remains bundled as a resource. The [image entrypoint source](https://raw.githubusercontent.com/gvenzl/oci-oracle-free/main/container-entrypoint.sh) documents the initialization-script execution path.
- **Issue disposition:** Separate-process resource configuration adaptation; resource staging/documentation could improve. The SQL file exists and application-side resource loading is verified separately, but this does not establish a contract that the Test Resources server shares the application's classpath.

### PORT-031 — Reference pet/visit operations do not enforce owner-path membership

- **Observed:** In the running Java reference, GET `/owners/2/pets/1/edit` and `/owners/2/pets/1/visits/new` return 200 and display pet 1 with its actual owner. A valid JSON visit POST and valid pet edit POST through owner 2 both return 301 to `/owners/2`; restoring the pet through owner 1 returns 301 to `/owners/1`. The source resolves the pet independently of `ownerId`; pet edit POST assigns the URL's owner, and visit POST saves against the selected pet and redirects to the URL's owner.
- **Impact:** The added membership checks in the initial port change the requested clean copy's behavior. This is also a reference application concern if stronger parent ownership semantics are desired later.
- **Resolution:** Remove the port-only rejection checks and preserve reference lookup/reassignment behavior. The interval check verifies a mismatched-owner visit POST, its redirect, the actual owning pet's updated history, and both mismatched-owner GET pages. A separate runtime check of pet reassignment in the port remains part of the broader contract audit.
- **Issue disposition:** Reference behavior, not an SDK defect. Do not silently introduce additional authorization/ownership policy into this port.

### PORT-032 — Running reference has core validation/error response defects

- **Environment:** Unmodified local reference copied to an isolated temporary directory; `./gradlew classes --offline` succeeded; `MICRONAUT_SERVER_PORT=18081 ./gradlew run --offline` started the default H2 application.
- **Reproduction A:** POST JSON to `/owners/1/pets/1/visits/new` with `{"date":"2031-02-03","description":"golden invalid","durationMinutes":0,"followUpPeriodMonths":6}`. Response is 500 JSON. The trace shows the local validation handler reads query parameters for IDs that are supplied as path variables, passes a null owner to the JTE view, and the renderer throws `NullPointerException` at `owner.id()`.
- **Reproduction B:** POST URL-encoded empty owner fields to `/owners/1/edit`. Response is 500 HTML containing the creation form action `/owners/new`. The source's shared validation handler unconditionally sets `isNew=true`.
- **Reproduction C:** POST a valid URL-encoded visit body to the JSON-only visit route. The running reference returns 500 HTML; its error log contains `AuthorizationException`. This does not imply that form-encoded visit creation is supported.
- **Control:** A valid pet form with nonexistent `typeId=999999` returns 400 and body `Invalid pet type`; this is distinct from a constraint-validation failure.
- **Disposition:** Reference application defects and framework response behavior. Report separately from Pyronaut candidates. The port's remaining validation-status/body comparison is explicitly open; successful workflows and captured successful JSON contracts do not prove these failure paths match.

### PORT-035 — Dialect repository subclasses lose inherited CRUD generic signatures

- **Observed:** Translating the reference's shared unannotated repository interfaces plus per-dialect `@JdbcRepository` subclasses failed during Python processing. Generated Java implementations contain methods such as `deleteAll(Iterable<Visit>)` and `<S> saveAll(Iterable<Visit>)`; the inherited Micronaut interfaces require `Iterable<? extends Visit>` and bounded generic `S` signatures. Java compilation reports missing overrides and erasure clashes across the dialect subclasses.
- **Reproduction:** Declare `VisitRepository(CrudRepository[Visit, int], Protocol)` without a JDBC annotation, then `@JdbcRepository(dialect=Dialect.MYSQL) class MySqlVisitRepository(VisitRepository, Protocol)` and process it. The same structure compiled in the Java reference.
- **Evidence:** Local processor dump `__pyronaut__/processor-error-dumps/pyronaut-compiler-error-20261016-134859-845.log`; generated `MySqlVisitRepository.java`.
- **Impact:** A direct translation of the reference repository organization does not compile with this SDK, before any database startup.
- **Workaround (verified across all profiles):** A direct CRUD base alone did not correct the generated signatures while the peer contract still inherited CRUD. Use `GenericRepository[Entity, int]` for the shared query contract and declare `CrudRepository[Entity, int]` directly on each dialect implementation. This retains the actual generated CRUD methods on the injected implementation and avoids the SDK's broken nested generic bridge path. Combined with PORT-039's explicit query declarations, runtime injection, CRUD, facade deletes and shared HTTP workflows pass on Oracle, H2, PostgreSQL and MySQL.
- **Issue disposition:** SDK nested generic interface/bridge generation candidate. Preserve the actual generated repository mechanisms while finding a working declaration shape.

### PORT-038 — Reference H2 generated price column loses fractional amounts

- **Observed:** The running reference's schema log contains `PRICE DECIMAL NOT NULL`, without a scale. A reduced check with the resolved H2 `2.4.240` driver creates that column, inserts `65.10`, and reads back `65`.
- **Reproduction:** `CREATE TABLE PRICE_PROBE (PRICE DECIMAL); INSERT INTO PRICE_PROBE VALUES (65.10); SELECT PRICE FROM PRICE_PROBE;`.
- **Impact:** The source form permits two fractional digits and uses `BigDecimal`, but that generated H2 storage declaration discards them. This is a reference schema problem, not evidence of floating-point conversion in Python.
- **Port adaptation:** New dialect migrations explicitly use `DECIMAL(10, 2)`, as the existing Oracle migration does, to preserve the declared price contract. Catalog round trips preserve fractional prices on H2, PostgreSQL and MySQL. This storage difference must be considered when comparing the source's defective H2 decimal behavior.
- **Issue disposition:** Reference mapping/schema candidate. File with the source DDL and reduced driver result; no source checkout was edited.

### PORT-039 — Shared Python query declarations do not retain each child's SQL dialect

- **Observed:** After resolving generic bridge compilation, H2 startup, fixture seeding, generated spatial searches and Oracle feature gating worked. Some inherited query methods still executed SQL from a different specialization: pet/vet lookups used PostgreSQL-style double-quoted lower-case `id`, and catalog relationship queries invoked Oracle's `SDO_UTIL.TO_GEOJSON` on H2.
- **Evidence:** H2 suite ran 16 shared cases; six failed. The catalog trace reports `Schema "SDO_UTIL" not found`; its SQL contains Oracle geometry projection functions despite selecting the H2 repository bean. Both PostgreSQL-style ID lookups and Oracle geometry projections appear in the same H2 context.
- **Impact:** Successful bean selection and compilation do not establish correct inherited query metadata. This is independent of H2GIS availability: generated nearby/within/intersection checks passed.
- **Workaround (verified across all profiles):** Redeclare the same annotated custom query signatures on each dialect implementation so each declaration has a distinct owning type. Keep shared query contracts for injection and generated CRUD directly on the concrete implementations. All 16 shared checks pass on H2, PostgreSQL and MySQL, and all 26 Oracle checks pass, including the previously failing lookup and joined catalog paths. Spatial and upsert operations still use Micronaut Data generation; they were not replaced by custom persistence code.
- **Issue disposition:** SDK/Micronaut Data Python inherited query ownership/metadata specialization candidate. Reduce with one shared query, two dialect subclasses and inspection of both generated SQL definitions.

### PORT-040 — JUnit suite summary reports zero skips despite skipped cases

- **Observed on SDK 0.1.1:** The H2 CLI reports 101 passed / 20 skipped. Its XML contains 121 test cases and twenty `<skipped>` elements, but the suite attribute is `skipped="0"`.
- **Evidence:** `__pyronaut__/reports/refactor-20261028/final/h2/junit.xml`; the individual skipped elements identify the Oracle-only cases.
- **Impact:** Tools relying on suite-level skip counts can report misleading coverage totals. This does not establish Oracle feature coverage on H2.
- **Workaround:** Count actual child results and use the CLI summary when reporting profile coverage.
- **Issue disposition:** Remaining SDK pytest/JUnit skip-count consistency candidate. Reduce with one unconditional `pytest.skip` before filing. The older total-case and duplicate-parameter-name problems are resolved in this SDK and are no longer issue candidates here.

### PORT-042 — Core fixture migrations bypass the sample-data configuration switch

- **Observed by source/configuration comparison:** The Java `DataLoader` is conditional on `petclinic.sample-data.enabled=true` (default true). The Python vector loader preserves that condition, but core/clinic/appointment SQL fixture migrations execute independently of it, including the new dialect seed migrations.
- **Impact:** Setting the flag false does not produce the reference's empty shared tables in a new database. Successful checks using the default enabled setting do not establish this configuration contract.
- **Required work:** Separate conditional fixture loading from schema creation for new profiles and reconcile the existing applied Oracle seed history without rewriting checksums or deleting user-created rows. Verify both enabled and disabled startup and restart behavior.
- **Issue disposition:** Port configuration/lifecycle parity gap, not an upstream SDK defect. Still open.

### PORT-043 — Conditional fixture-loader experiment fails resource lookup

- **Observed:** An attempted separation of schema migrations from conditional sample-data loading failed the dedicated H2 lifecycle test with `ValueError: Missing application resource: data/petclinic-sample.json`. The disabled-startup checks completed before enabled startup attempted to read that resource.
- **Reproduction at the time:** In the isolated matching GraalPy checkout, run `PETCLINIC_TEST_DATABASE=h2 pyronaut test --no-validate --tests '*sample_data*'`. One selected test failed in 10.7s. It used a fresh H2 schema, a JSON file under `config/data/`, baseline schema snapshots and a conditional transactional startup seeder.
- **Impact:** The experiment did not establish successful enabled startup or restart preservation. An earlier ordinary H2 run was insufficient evidence of the loader's lifecycle behavior.
- **Stabilization action:** Remove the experimental loader, JSON data, baseline snapshots, corrective fixture migrations and lifecycle assertions. Retain the previously passing versioned schema/SQL seed migrations. The experimental code is not part of this checkpoint; the command above therefore no longer reproduces it in the current tree.
- **Evidence:** Failure log and JUnit report were preserved locally under `__pyronaut__/reports/deferred-fixture-experiment/`. These generated artifacts are ignored by Git.
- **Later work:** First reduce whether resource copying, generated-source caching or application resource visibility caused the missing stream. Use the supported `Environment` resource path, prove the file is in processed resources, then test disabled startup, enabled startup and restart separately. Isolate lifecycle databases from the ordinary suite. Do not rewrite applied Flyway checksums or delete user-created data.
- **Issue disposition:** Unresolved experiment/integration failure; no upstream SDK defect established. Deferred with PORT-042.

## Deferred work for later

These items are documented proposals, not implemented additions or current stabilization tasks. Resume them only when requested.

| Work | Proposed approach | Acceptance check |
| --- | --- | --- |
| Conditional sample data (PORT-042/043) | Prove resource packaging first; separate new-schema creation from conditional transactional loading; design an upgrade path for existing databases | Fresh disabled startup has empty shared tables; enabled startup loads canonical fixtures; restart/repeated loading preserves user rows and creates no duplicates, across all four profiles |
| Remaining fixture audit | Compare other canonical fields if further parity work is requested | Compare complete records, not only filtered searches; preserve applied checksums and user-created data |
| Remaining source contracts (PORT-031/032) | Audit model identity/helper behavior, service/repository signatures, cross-owner writes and error/content-type responses against the running reference | Record exact request/status/body or model behavior; distinguish reference bugs from port defects before changing behavior |
| Concurrent first catalog insert | Submit overlapping writes for a previously absent clinic/code, retaining generated upsert and uniqueness | One persisted row and identity; responses follow the chosen reference contract; no partial combined row |
| Browser and visual parity | Compare locale switching, forms, maps, catalog pages, care editor and priority interactions with the reference | Manual browser evidence, including unavailable CDN assets and JavaScript-driven results |
| Distribution and production configuration | Exercise packaged startup away from the repository root, resource/static loading and external datasource overrides/fallbacks; review management endpoints against the reference | Packaged routes/assets/resources work; configured database connections resolve correctly; intended health/security behavior matches the source |
| CI verification | Review SDK configuration validation and execute the configured four-profile remote CI matrix | Explicit validation result; successful remote jobs with honest skip counts |

Keep the source reference checkout and the user's existing CPython environment unchanged. Continue using already cached images locally.

## Other verification notes

- Full browser behavior and visual parity with the reference after JTE-to-Jinjava translation.
- Concurrent catalog insertion of an absent natural key. Updates to an existing key and actual veterinarian cache reuse/invalidation now have passing checks.
- JSON duality and transaction priority now have passing runtime checks described below. All four database profiles have runtime coverage. Fixture lifecycle, packaged execution and the remaining model/service and HTTP contract comparison are still open work; missing coverage is not an upstream defect claim.

## Previous verification checkpoint (2026-10-16)

2026-10-16 stabilization rerun: **26 integration tests passed in 49.8s** against the cached Oracle image after removing the unfinished fixture-loader experiment. The cases include ordinary PetClinic workflows, captured Java-reference vet/owner-search JSON contracts, spatial queries, catalog upserts, visit bounds, locale switching, HTML 404s, ranked vectors, nested duality updates, date/null validation, insert/delete restrictions, stale ETAGs after document and relational edits, and JSON not-found responses.

Priority checks additionally establish regular commit, taken/missing/reset responses, actual overlapping LOW/HIGH HTTP requests with an independent probe observing LOW's Oracle row lock before HIGH, emergency commit with LOW priority rollback, outcome classification, and an actual equal-priority `FOR UPDATE WAIT 10` timeout. Database configuration is applied automatically by the container initializer; no privileged test setup remains.

The latest suite additionally verifies all-pet and visit/vet/speciality ID lookups, enriched veterinarian service results, speciality join lookup, and a create/look-up/delete facade workflow for an owner, pet and visit. The cache check mutates a vet row through independent JDBC, observes the cached old value through JSON, HTML and the service, invalidates the cache, and observes the new value before restoring the row. Six asynchronous HTTP catalog updates preserve the original identity and a single complete submitted row.

Additional profile results: **H2 16 passed / 10 Oracle-only skips (16.7s)**; **PostgreSQL 16 passed / 10 skips (20.1s)**; **MySQL 16 passed / 10 skips (24.9s)**. Database-product checks confirm each actual driver, and Oracle-only routes/services are absent on the other profiles. Each uses the same shared spatial, catalog, CRUD, caching and localization checks. Final stabilization reports and command logs are preserved under `__pyronaut__/reports/stabilization/`; earlier reports remain under `__pyronaut__/reports/database-profiles/`. Counts use child test elements because of PORT-040. All four final suites have zero failures/errors.

Python source and TOML parsing and `git diff --check` also pass. Experimental loader code, lifecycle tests and unapplied experimental migration files were removed from both the repository and the isolated test copy. Original applied Oracle migration files and the user's staged `.gitignore` change were preserved. No new local image pulls, external issue filings or remote CI runs were performed.

Interactive browser parity, concurrent insertion of an absent clinic/code, fixture/sample-data lifecycle alignment, remaining model/service/repository and HTTP failure-path fidelity checks, production URL fallback execution, and packaged execution remain outside this checkpoint. SDK configuration validation was skipped. Full reference parity is not claimed; further implementation is deferred at the user's request.

## Findings from the 2026-10-26/27 review

### PORT-045 — Nullable collection elements cross the boundary as zero or foreign nulls

- **Observed:** `specialityIds: list[int | None] | None` bound `[null]` as a value that produced the unknown-ID error rather than the source's missing-ID error. An explicit Java `Integer` type did not correct that conversion. Binding as an object collection preserved a `ForeignNone` value, whose identity differs from Python `None`.
- **Impact:** A straightforward DTO translation can lose null semantics. Converting arbitrary object inputs to a set before type validation can also fail on nested arrays/maps.
- **Workaround:** Bind the collection at the object boundary, check Python/foreign nulls directly, reject non-integer/boolean/out-of-range values before set construction, then resolve distinct persisted IDs. Preserve the source's 400 messages. HTTP tests cover null elements, null/empty selections, nested values and the integer boundary.
- **Disposition:** SDK null/collection conversion candidate. Reduce with one nullable collection DTO before assigning ownership or filing. Explicit validation is an application adaptation.

### PORT-046 — Generated PostgreSQL ETag expression does not quote mapped identifiers

- **Observed:** H2 and Oracle ETag CRUD worked. PostgreSQL then failed 24 shared checks with `ERROR: column vet_.first_name does not exist`. The mapped columns are quoted uppercase names; the synthesized ETag read expression references their unquoted names, which PostgreSQL folds to lowercase.
- **Resolution:** `db/postgres/V5__etag_identifier_aliases.sql` adds computed lowercase aliases for first name, last name and the speciality hash. They derive from the canonical columns and cannot be independently changed. The ORM still generates and enforces the ETag predicate; no Python compare-then-write replacement was introduced.
- **Evidence:** The first corrected PostgreSQL run passed all 84 then-current shared cases, including stale link rollback; final coverage is recorded below. Initial failures are preserved under `__pyronaut__/reports/review-20261026/postgres-initial/`.
- **Disposition:** Micronaut Data generated ETag transformer/identifier quoting candidate. Reduce on both Java and Python before claiming it is Python-specific.

### PORT-051 — Embedded pytest default capture aborts before test execution

- **Observed (2026-10-28):** The pre-refactor suite on Pyronaut `0.1.1`, Core `5.2.19` and matching GraalPy `25.4.4.1.1` processes successfully after PORT-018's compatibility adaptation, then aborts with `FileNotFoundError: [Errno 2] No such file or directory` through pytest/pluggy. The CLI reports `No tests ran, 82 errors`; these are one runner startup failure, not 82 application defects.
- **Control:** The same two assertion-only hash tests pass with `PYTEST_ADDOPTS='--capture=sys --full-trace'`; no application/database change is involved.
- **Workaround:** Configure `[tool.pytest.ini_options] addopts = '--capture=sys'` in `pyproject.toml`. Stream capture retains Python output without pytest's default file-descriptor capture. The missing path and exact runtime ownership still need a minimal reproduction.
- **Evidence:** Local logs `/private/tmp/pyronaut-refactor-compatibility-h2.log` and `/private/tmp/pyronaut-refactor-runner-probe.log`. No upstream framework code was changed.

### PORT-052 — Custom Python exception classification fails across a service boundary

- **Observed on SDK 0.1.1:** After separating the priority service and controller, the real already-taken booking request returns HTML 500 instead of JSON 409. The service's custom `BookingTaken` exception reaches the controller as its generated Java mirror; Python classification fails with `AttributeError: foreign object has no attribute '__micronaut_python_object__'`.
- **Evidence:** The initial Oracle matrix passes 119 cases and fails only `test_priority_booking_commits_and_reports_taken_appointments`. Logs and XML are retained under `__pyronaut__/reports/refactor-20261028/oracle-initial/`; the corrected full run is archived under `final/oracle/`. Other priority overlap/rollback checks pass.
- **Workaround (focused HTTP check and full Oracle suite passed):** Recognize `java.type('petclinic.models.BookingTaken')` before checking the Python `BookingTaken` class. Keep native Python classification for local exceptions. The original end-to-end booking/taken/reset test then passes without changing service transactions or response expectations.
- **Issue disposition:** Generated exception-mirror/inter-context integration candidate. Reduce across two small modules before assigning the exact framework owner; this was observed with the new package boundaries, not proven to affect every custom exception or older SDK release.

### PORT-053 — Pytest fixture misses the application context configurer

- **Classification:** Framework candidate; Pyronaut pytest context-builder/classloader integration.
- **Observed on SDK 0.1.1:** With only the `test` environment, the fixture has neither the default dialect nor a datasource. The application configurer runs during CLI configuration validation but is not invoked for the pytest application context. The new dialect-based repository conditions expose the missing default explicitly.
- **Mechanism evidence:** Installed `PytestMicronautExtension$PytestApplicationContextBuilder` bytecode calls the no-argument base-builder constructor before `configureApplicationClassLoader`. Core loads `ApplicationContextConfigurer` implementations in that base constructor, using the earlier classloader. Configuring the classloader afterward does not reload them. Preserve a reduced sentinel-property comparison before filing upstream.
- **Workaround:** Select `environments=["test", DATABASE]` for all HTTP/database matrix runs, including H2. Check the profile-free H2 fallback separately with `ApplicationContext.builder(applicationClassLoader)`; do not restore environment-based repository conditions.
- **Evidence:** The initial full H2 run failed 85 of 106 executed cases; its profile check had no configured dialect and no datasource. Reports are retained under `__pyronaut__/reports/dialect-selection-20261028/initial/`. Focused failure logs and inspected SDK builder bytecode are retained locally in `/private/tmp/pyronaut-dialect-fallback-debug.log` and `/private/tmp/pyronaut-pytest-extension-bytecode.txt`.

### PORT-054 — Reused Oracle sessions can lose later priority-rollback failures

- **Classification:** Unresolved between Oracle database and JDBC driver; reproduced without Pyronaut, Micronaut, Hikari or the browser. This is not classified as a Python framework defect or an environment provisioning problem.
- **Verified versions:** Cached Oracle Free `23.26.2.0.0` (`gvenzl/oracle-free:23.26.2-faststart`) with Oracle JDBC `23.26.3.0.0`. The PDB has `priority_txns_mode=ROLLBACK` and both wait targets set to 3 seconds.
- **Reproduction:** Keep a LOW and HIGH JDBC connection open across three booking races. LOW holds a row and pauses for the real 15-second demo interval; HIGH updates the same row after one second. The first LOW request receives ORA-63302. Reusing the same sessions for races two and three instead lets LOW update and commit after HIGH already committed, leaving `BOOKED_FOR_REGULAR`. The live development app and repeated HTTP regression reproduce the same incorrect final row and two `COMMITTED` responses.
- **Expected contract:** Oracle documents ORA-63300/63302 until rollback acknowledgement; the displaced transaction must not silently continue and overwrite HIGH. See [Oracle's priority-transaction acknowledgement documentation](https://docs.oracle.com/en/database/oracle/oracle-database/26/admin/managing-transactions.html).
- **Coverage correction:** The previous HTTP suite tested one displacement using a shortened 5-second pause. It did not establish that subsequent priority rollbacks remain reliable on reused sessions. Tests now use the application default of 15 seconds, repeat the overlap three times, and check persisted state after both requests finish.
- **Application workaround:** `OraclePriorityConnectionCleanup` registers a connection callback only for LOW Oracle-priority transactions. After Micronaut completes transaction cleanup and before the connection returns to Hikari, it retires that one physical connection. HIGH and ordinary transactions retain pooling. This deliberately spends a new connection on each LOW demo attempt; it preserves real Oracle rollback exceptions and does not fabricate a UI outcome or retry the losing write. Remove the workaround only after the repeated JDBC and HTTP reproductions pass with session reuse on corrected Oracle/driver versions.
- **Evidence:** Original live responses, Oracle trace, repeated raw JDBC source/output and failing HTTP reports are retained locally under `__pyronaut__/reports/priority-overlap-20261028/before/`. The existing demo appointments were left unchanged; temporary live diagnostic rows were removed.

## Latest verification checkpoint

The final **2026-10-28** runs collected 133 cases per profile, with zero failures/errors. They used Pyronaut **0.1.1**, Core **5.2.19**, Data **5.2.3**, Serialization **3.2.5**, Validation **5.2.1**, Test Resources client **4.3.1** and matching GraalPy **25.4.4.1.1**. After the priority-session cleanup, all four profiles were rerun. Oracle uses the default 15-second reservation pause and repeats the displacement race three times. The latest reports, CLI logs and source-content manifest are retained locally under `__pyronaut__/reports/priority-overlap-20261028/final/`; preceding dialect and package checks remain under `__pyronaut__/reports/dialect-selection-20261028/final/`, `__pyronaut__/reports/models-dtos-20261028/final/` and `__pyronaut__/reports/refactor-20261028/`.

| Profile | Passed | Expected skips |
| --- | ---: | ---: |
| H2 | 107 | 26 Oracle-only cases |
| Oracle | 132 | 1 H2-only case |
| PostgreSQL | 106 | 26 Oracle-only and 1 H2-only case |
| MySQL | 106 | 26 Oracle-only and 1 H2-only case |

The existing local Java reference advanced from `0ad5747` to `f0e444e`. Its seven changed files contain dependency/build updates only: no application code, tests, templates or resources changed. Maven/Gradle parent settings, Java native-build metadata and the Java CI GraalVM action are not copied into the SDK-managed Python build. This check validates the port on the installed SDK stack; dependency versions are not claimed to be identical to the Java build.

Repositories, services, controllers, domain/persistence models and request/response DTOs are now separate namespace packages organized by functionality. The package split preserved all 103 Python classes and their domain fields and method bodies; imports and explicit Java mirror lookups follow the new packages. Conditional repository, service and controller annotations now use shared constants for `datasources.default.dialect`; Oracle navigation uses that same property. Explicit concrete query declarations, generated CRUD/ETag predicates, singleton service scopes and transaction annotations remain intact. The profile check asserts both the live database product and JDBC URL. H2 settings live in a separate configuration file and are loaded only as a fallback when no datasource dialect is configured; external profiles contain no inherited H2 connection settings. Six bean-selection checks per run verify the profile-free H2 fallback, explicit H2/MySQL/Oracle/PostgreSQL dialects under custom profiles, and an Oracle profile overridden by an H2 dialect. Flat, nested and environment-style property sources are covered. The HTTP fixture selects H2 explicitly because of PORT-053.

A plain `pyronaut dev` startup with no database environment used H2, served health/vets/clinics, and kept Oracle-only care records unavailable (404). A real `MICRONAUT_ENVIRONMENTS=oracle pyronaut dev` startup opened an Oracle connection, applied all 17 migrations, and served health, vet JSON, care-record JSON and the priority page with HTTP 200. `pyronaut run dev` passes an application argument; this SDK starts Test Resources for `dev`/`test`, while `run` requires an existing database connection.

Configuration validation is enabled with the single documented Test Resources suppression. Existing cached images were reused. Core sample-data lifecycle parity, model/helper equivalence, concurrent first catalog insertion, interactive browser behavior, packaged execution and remote CI remain outside this checkpoint. No external issues or remote pushes were created.

Earlier priority-page checks restored the missing JavaScript module from the local Java reference. A new HTTP regression follows the page's local script references and checks successful delivery with a JavaScript content type. The full Oracle follow-up collected **128 cases: 127 passed, 1 expected H2-only skip, zero failures/errors**, including regular booking, emergency displacement, lock timeouts and reset. Reports, CLI output and tested source hashes are retained locally under `__pyronaut__/reports/priority-ui-20261028/oracle/`. JavaScript syntax validation passed, and the running development server served the restored module with HTTP 200. Browser click verification remains outside this check.

The next priority-page check found 19 missing English messages, also absent from the local Java reference's base bundle. English now supplies the same outcome and summary meanings as the existing Spanish/German translations. All 37 priority message keys are present in each language; existing reference translations, the booking script and page IDs/classes are preserved. HTTP regressions use the locale selector and verify all 20 browser status labels, including the committed-booking caption, in English, Spanish and German. The full Oracle follow-up collected **131 cases: 130 passed, 1 expected H2-only skip, zero failures/errors**. Reports and tested source hashes are retained locally under `__pyronaut__/reports/priority-labels-20261028/final-oracle/`. The running development page also served the restored English captions.

PORT-054 verification also exercised two consecutive overlapping bookings against the running development application. Both runs returned HTTP 200/`COMMITTED` for HIGH and HTTP 409/`PRIORITY_ROLLED_BACK` for LOW, and both final rows remained `BOOKED_FOR_EMERGENCY`. The LOW sessions were retired after cleanup. Existing demo bookings were left unchanged and temporary diagnostic rows were removed. Live response timelines are retained under `__pyronaut__/reports/priority-overlap-20261028/live-after/`. This verifies real request outcomes and persisted rows; it does not claim automated browser clicks.
