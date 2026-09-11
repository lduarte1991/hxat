## Why

The seed JSON exported by `exportcourse` includes production annotation-database credentials (`annotation_database_url`, `annotation_database_apikey`, `annotation_database_secret_token`) for every assignment. When those records are imported into a development or staging environment, all assignments point at the production catchpy instance instead of the local one, silently corrupting the seeded environment.

## What Changes

- `importcourse` gains three optional flags: `--annox-db-url`, `--annox-db-key`, and `--annox-db-secret`.
- When any of these flags is supplied, the corresponding field is overwritten on every `Assignment` record during import, regardless of the value in the seed file.
- If a flag is omitted, the seed file value for that field is used unchanged (existing behaviour).
- All three flags may be supplied together or independently.

## Capabilities

### New Capabilities

- `course-import-annox-override`: Override annotation-database credentials on imported assignments with environment-specific values.

### Modified Capabilities

- `course-import`: The three new override flags extend the existing import command's behaviour; the natural-key upsert and summary requirements are unchanged.

## Impact

- Modified file: `utils/management/commands/importcourse.py`
- No migrations required
- No change to the export format or `exportcourse.py`
- No other commands or views affected
