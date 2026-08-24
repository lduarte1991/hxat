## Why

Seeding a development or staging database currently requires manually trimming a production dump — a slow, non-repeatable process that leaves orphaned records and cannot be version-controlled. We need a reliable, repeatable way to seed a fresh database with a representative subset of real courses and their full dependency graph.

## What Changes

- New `exportcourse` management command: given a list of course IDs, collects the full graph (courses, assignments, assignment targets, and target objects) and writes a custom JSON file.
- New `importcourse` management command: reads that JSON file and upserts all records into the target database using natural keys, making it resilient to schema changes between export and import. Creates a fixed `seed-loader` identity (`auth.User` + `LTIProfile`) to attribute `TargetObject.target_creator` on import.
- Custom JSON format (not Django fixtures) to avoid `loaddata` brittleness on schema evolution.

## Capabilities

### New Capabilities

- `course-export`: Export a representative set of courses and their full dependency graph to a JSON seed file.
- `course-import`: Import a seed JSON file into a target database using natural-key upserts, handling schema drift gracefully.

### Modified Capabilities

## Impact

- New files: `utils/management/commands/exportcourse.py`, `utils/management/commands/importcourse.py`
- Touches: `hx_lti_initializer` models, `hx_lti_assignment` models, `target_object_database` models
- No migrations required
- No existing commands or views affected
