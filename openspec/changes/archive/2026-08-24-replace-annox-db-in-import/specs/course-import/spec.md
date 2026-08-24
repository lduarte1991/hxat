## ADDED Requirements

### Requirement: Accept optional annotation-database override flags
The command SHALL accept `--annox-db-url`, `--annox-db-key`, and `--annox-db-secret` as optional arguments. When present, they override the corresponding fields on imported assignments (see `course-import-annox-override` capability). When absent, the command behaves exactly as before this change.

#### Scenario: Flags provided
- **WHEN** the command is invoked with one or more of `--annox-db-url`, `--annox-db-key`, `--annox-db-secret`
- **THEN** the supplied values overwrite the matching credential fields on every imported `Assignment`

#### Scenario: Flags not provided
- **WHEN** the command is invoked without any of the three flags
- **THEN** the import proceeds with credential values taken from the seed file unchanged
