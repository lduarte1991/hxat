## Purpose

Allows the `importcourse` command to overwrite annotation-database credentials on imported assignments with environment-specific values, preventing seeded environments from accidentally pointing at production catchpy.

## ADDED Requirements

### Requirement: Accept annotation-database override flags
The command SHALL accept three independent optional flags:
- `--annox-db-url`: overrides `annotation_database_url` on every imported `Assignment`
- `--annox-db-key`: overrides `annotation_database_apikey` on every imported `Assignment`
- `--annox-db-secret`: overrides `annotation_database_secret_token` on every imported `Assignment`

Each flag is independent — any combination of zero, one, two, or all three may be supplied in a single invocation.

#### Scenario: All three flags supplied
- **WHEN** the command is invoked with `--annox-db-url`, `--annox-db-key`, and `--annox-db-secret`
- **THEN** every imported `Assignment` record has all three credential fields set to the supplied values, regardless of what was in the seed file

#### Scenario: Subset of flags supplied
- **WHEN** only `--annox-db-url` is supplied (or any other single flag)
- **THEN** `annotation_database_url` is overwritten on every imported `Assignment`; the other two fields retain their seed-file values

#### Scenario: No override flags supplied
- **WHEN** none of the three flags is supplied
- **THEN** the import proceeds identically to the pre-change behaviour; all three credential fields are taken from the seed file unchanged

### Requirement: Override applied to every assignment in the run
When an override flag is supplied, the command SHALL apply the override value to every `Assignment` record imported in that run — both newly created records and records updated via `update_or_create`.

#### Scenario: New assignment
- **WHEN** an `Assignment` is created during import and `--annox-db-url` is supplied
- **THEN** `annotation_database_url` on the created record equals the supplied value

#### Scenario: Existing assignment updated
- **WHEN** an `Assignment` already exists and is updated during import and `--annox-db-url` is supplied
- **THEN** `annotation_database_url` on the updated record equals the supplied value
