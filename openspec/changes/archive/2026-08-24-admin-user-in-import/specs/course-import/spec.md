## ADDED Requirements

### Requirement: Accept optional admin profile flag
The command SHALL accept an optional `--admin-profile-name` argument. When present, its value is used to resolve or create an admin identity (see `course-import-admin` capability). When absent, the command behaves exactly as before this change.

#### Scenario: Flag provided
- **WHEN** the command is invoked with `--admin-profile-name <name>`
- **THEN** the named identity is resolved or created and added as admin to all imported courses

#### Scenario: Flag not provided
- **WHEN** the command is invoked without `--admin-profile-name`
- **THEN** the import proceeds identically to the pre-change behaviour; no `course_admins` entries are set
