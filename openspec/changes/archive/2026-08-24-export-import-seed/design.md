## Context

The app has three Django apps with the relevant models: `hx_lti_initializer` (LTICourse, LTIProfile), `hx_lti_assignment` (Assignment, AssignmentTargets), and `target_object_database` (TargetObject). Existing management commands (`delcourse`, `dbreport`) in `utils/management/commands/` follow the same pattern this change extends.

The key graph complication: `TargetObject` has a `target_courses` M2M that can reference courses outside the export set, and its integer PK is the only stable identity (no UUID, no unique business key).

See `proposal.md` for motivation.

## Goals / Non-Goals

**Goals:**
- Two standalone management commands: `exportcourse` and `importcourse`
- Export produces a self-contained JSON file, not Django fixture format
- Import is idempotent and handles schema drift without crashing
- No new migrations or model changes

**Non-Goals:**
- Exporting or importing annotation data from the external annostore (catchpy)
- Anonymizing or transforming exported data
- Merging exports from multiple sources
- Providing a UI or API endpoint for export/import

## Decisions

### Custom JSON format over Django fixtures

Django fixtures embed Django's internal serialization format and are tightly coupled to the exact schema at export time. `loaddata` fails with `DeserializationError` on unknown fields and `IntegrityError` on missing required fields. Our format is a plain dict per model; the import command controls which fields it reads, ignoring unrecognized ones via a simple `pop`/`get` pattern on the incoming dict.

Alternatives considered: `dumpdata --natural-foreign` — still Django fixture format with the same fragility; `pg_dump` table-level — not portable across schema versions.

### TargetObject identity: integer PK from export

`TargetObject` has no UUID or unique business key. Within a single export/import cycle, the PK is stable and internally consistent. The import uses `update_or_create(pk=<exported_pk>)` to upsert.

This means: if a `TargetObject` PK from the seed file collides with an unrelated object already in the target DB, the import will overwrite it. Acceptable for the dev/staging seeding use case; the target DB is typically fresh or already seeded from a previous run of the same file.

Alternatives considered: composite pseudo-key (`title + type + content_hash`) — avoids the PK collision risk but breaks on title/content edits and adds complexity. Adding a UUID field to the model — cleanest long-term, but requires a migration, which is out of scope.

### Import field handling: explicit field mapping

Rather than using Django's deserializer (which rejects unknown fields), the import command explicitly maps JSON keys to model field kwargs using a helper that builds the `defaults` dict and skips any key not present in `model._meta.get_fields()`. This makes schema drift safe in both directions (added fields get DB defaults; removed fields are silently ignored).

### seed-loader identity for TargetObject.target_creator

`TargetObject.target_creator` is a FK to `LTIProfile` (SET_NULL). Prod profiles are not exported, so importing with `target_creator=null` would work but loses the FK entirely. Instead, the import command creates a fixed synthetic `auth.User` (`username=seed-loader`, `is_staff=False`) and `LTIProfile` (`anon_id=seed-loader`, `scope=seed`) via `get_or_create`, and assigns it as `target_creator` on all imported target objects.

This identity is hardcoded (not configurable) to keep the import simple and predictable. The synthetic scope `"seed"` does not collide with real LTI scopes (which are LMS course instance IDs or domain values). The `is_staff=False` choice is intentional: `TargetObject` query methods gate on `is_staff`, and the loader identity should not grant unexpected admin access.

### Export serialization: model-by-model collect, then deduplicate

The exporter iterates courses, collects each subgraph into typed lists, and deduplicates by PK before serializing. This is simpler than a recursive graph walker and sufficient given the shallow, well-known graph shape.

## Risks / Trade-offs

**PK collision on TargetObject** → The target DB should be a fresh DB or a DB previously seeded by the same file. Document this constraint in command help text.

**Large exports** → The command loads the full graph into memory before writing. For a reasonable representative set (tens of courses), this is fine. For hundreds of courses with many assignments and target objects, memory could become an issue. Not addressed in this design.

**`target_courses` M2M trimming** → The export serializes each `TargetObject`'s `target_courses` as the intersection of its actual courses and the exported course set. The import re-adds only those M2M entries. If a `TargetObject` was also used in a non-exported course that exists in the target DB, that cross-reference is not restored — which is correct for a seed scenario.

## Migration Plan

No migrations. Deploy by merging the two new command files. The commands are opt-in (management commands only); nothing runs automatically.

Rollback: delete the two command files. No data is affected.
