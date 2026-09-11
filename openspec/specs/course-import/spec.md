## Purpose

Provides a management command that reads a seed JSON file produced by `exportcourse` and upserts all records into the target database using natural keys, remaining functional even when the schema has evolved since the file was exported.

## Requirements

### Requirement: Create seed-loader identity
Before importing any records, the command SHALL ensure a fixed synthetic identity exists using `get_or_create`:
- `auth.User`: `username=seed-loader`, `is_staff=False`
- `LTIProfile`: `anon_id=seed-loader`, `scope=seed`, linked to that user

This identity is used as `target_creator` for all imported `TargetObject` records. It is never exported and carries no course membership.

#### Scenario: First import on empty database
- **WHEN** no `seed-loader` user exists
- **THEN** the user and profile are created before any other records are imported

#### Scenario: Re-import on existing database
- **WHEN** a `seed-loader` user already exists from a prior import
- **THEN** the existing identity is reused without modification

### Requirement: Accept seed file input
The command SHALL accept a `--input-json` argument pointing to a JSON file in the format produced by `exportcourse`.

#### Scenario: Valid seed file
- **WHEN** the command is run with `--input-json <path>` pointing to a valid seed file
- **THEN** all records in the file are upserted into the database

#### Scenario: Missing input argument
- **WHEN** the command is run without `--input-json`
- **THEN** the command exits with an error message

### Requirement: Upsert using natural keys
The command SHALL use `update_or_create` keyed on each model's natural identifier so that re-running the import is idempotent and schema evolution does not cause crashes on unrecognized fields.

Natural key mapping:
- `LTICourse` → `course_id`
- `TargetObject` → `id` (integer PK from export)
- `Assignment` → `assignment_id` (UUID)
- `AssignmentTargets` → `(assignment_id, target_object_id)`

`LTIProfile` and `auth.User` from prod are not imported. The import command creates one fixed synthetic identity — `username=seed-loader`, `anon_id=seed-loader`, `scope=seed`, `is_staff=False` — used solely as `target_creator` for all imported `TargetObject` records.

#### Scenario: Import on empty database
- **WHEN** the target database has no pre-existing records for the exported courses
- **THEN** all records are created and the import reports success

#### Scenario: Re-import unchanged seed file
- **WHEN** the same seed file is imported a second time without changes
- **THEN** no errors occur and record counts remain the same

#### Scenario: Import after schema adds a nullable column
- **WHEN** the seed file was exported before a new nullable column was added to a model
- **THEN** the import completes successfully; the new column receives its database default

### Requirement: Import order respects foreign keys
The command SHALL import records in dependency order to satisfy FK constraints:
1. `seed-loader` identity (`auth.User` + `LTIProfile`) via `get_or_create`
2. `LTICourse`
3. `TargetObject` (with `target_creator` set to the `seed-loader` profile)
4. `Assignment`
5. `AssignmentTargets`
6. `TargetObject.target_courses` M2M

#### Scenario: FK dependency satisfied before child record
- **WHEN** an `Assignment` record references a `LTICourse` that is also in the seed file
- **THEN** the course is created before the assignment, and no FK violation occurs

### Requirement: Unknown fields in seed file are ignored
If the seed file contains fields for a model that no longer exist in the current schema, the command SHALL silently skip those fields and continue.

#### Scenario: Seed file has removed field
- **WHEN** the seed file contains a field that was removed from the model in a migration
- **THEN** the import completes without error; the unrecognized field is discarded

### Requirement: Output summary
After completing the import, the command SHALL print a JSON summary including counts of created and updated records per model, and a list of any warnings encountered.

#### Scenario: Successful import summary
- **WHEN** the import completes without fatal errors
- **THEN** stdout contains a JSON object with `created`, `updated`, and `warnings` keys

### Requirement: Accept optional admin profile flag
The command SHALL accept an optional `--admin-profile-name` argument. When present, its value is used to resolve or create an admin identity (see `course-import-admin` capability). When absent, the command behaves exactly as before this change.

#### Scenario: Flag provided
- **WHEN** the command is invoked with `--admin-profile-name <name>`
- **THEN** the named identity is resolved or created and added as admin to all imported courses

#### Scenario: Flag not provided
- **WHEN** the command is invoked without `--admin-profile-name`
- **THEN** the import proceeds identically to the pre-change behaviour; no `course_admins` entries are set

### Requirement: Accept optional annotation-database override flags
The command SHALL accept `--annox-db-url`, `--annox-db-key`, and `--annox-db-secret` as optional arguments. When present, they override the corresponding fields on imported assignments (see `course-import-annox-override` capability). When absent, the command behaves exactly as before this change.

#### Scenario: Flags provided
- **WHEN** the command is invoked with one or more of `--annox-db-url`, `--annox-db-key`, `--annox-db-secret`
- **THEN** the supplied values overwrite the matching credential fields on every imported `Assignment`

#### Scenario: Flags not provided
- **WHEN** the command is invoked without any of the three flags
- **THEN** the import proceeds with credential values taken from the seed file unchanged
