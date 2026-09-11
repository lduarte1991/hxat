## Purpose

Allows the `importcourse` command to associate a named admin identity with every course created or updated during an import run, so that seeded environments have at least one browsable admin per course without requiring a manual post-import step.

## Requirements

### Requirement: Resolve or create admin identity
When `--admin-profile-name` is supplied, the command SHALL ensure the named identity exists before importing any records. The identity consists of:
- `auth.User` with `username` equal to the supplied name
- `LTIProfile` with `anon_id` equal to the supplied name, linked to that user

If either does not exist it SHALL be created via `get_or_create` using the supplied name as both `username` and `anon_id`. This mirrors the existing `seed-loader` identity pattern.

#### Scenario: Identity already exists
- **WHEN** an `auth.User` and `LTIProfile` with the supplied name already exist
- **THEN** the existing records are reused without modification

#### Scenario: Identity does not exist
- **WHEN** no `auth.User` or `LTIProfile` matching the supplied name exists
- **THEN** both are created before any course records are imported

#### Scenario: Flag omitted
- **WHEN** `--admin-profile-name` is not supplied
- **THEN** no admin identity is resolved or created, and `course_admins` is not modified

### Requirement: Add admin profile to all imported courses
The command SHALL add the resolved admin `LTIProfile` to `course_admins` for every `LTICourse` that is created or updated during the import run.

#### Scenario: Course created during import
- **WHEN** a course is created and `--admin-profile-name` is supplied
- **THEN** the resolved profile is present in that course's `course_admins` after import

#### Scenario: Course updated during import
- **WHEN** a course already exists and is updated during import and `--admin-profile-name` is supplied
- **THEN** the resolved profile is present in that course's `course_admins` after import (added if not already there)

#### Scenario: Admin already in course_admins
- **WHEN** the resolved profile is already a member of `course_admins` for a course
- **THEN** the import completes without error and no duplicate entry is created

### Requirement: Admin creation counted in import summary
The command's output summary SHALL reflect any `auth.User` or `LTIProfile` records created for the admin identity using the same `created`/`updated` counters used for other records.

#### Scenario: Admin identity created
- **WHEN** the admin `auth.User` and `LTIProfile` are newly created
- **THEN** the summary JSON includes them in the `created` counts

#### Scenario: Admin identity already existed
- **WHEN** the admin identity already existed and was reused
- **THEN** the summary JSON includes them in the `updated` counts
