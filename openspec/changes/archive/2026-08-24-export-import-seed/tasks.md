## 1. Export Command

- [x] 1.1 Create `utils/management/commands/exportcourse.py` with `add_arguments` accepting `--course-id`, `--input-json`, and `--output`
- [x] 1.2 Implement graph collector: for each course ID, query `LTICourse`, its `assignments`, each assignment's `AssignmentTargets`, and the referenced `TargetObjects`
- [x] 1.3 Deduplicate collected records by PK across all courses before serializing
- [x] 1.4 Serialize `TargetObject.target_courses` M2M trimmed to the exported course set only
- [x] 1.5 Write output JSON with top-level keys: `exported_at`, `courses`, `data` (with sub-keys: `courses`, `target_objects`, `assignments`, `assignment_targets`)
- [x] 1.6 Write to `--output` file if given, else to stdout; print summary to stderr when writing to stdout
- [x] 1.7 Emit a warning (not an error) for each course ID not found in the database and continue

## 2. Import Command

- [x] 2.1 Create `utils/management/commands/importcourse.py` with `add_arguments` accepting `--input-json`
- [x] 2.2 Implement `_safe_defaults(model, data_dict)` helper: build `defaults` kwargs by intersecting `data_dict` keys with `model._meta.get_fields()` field names, skipping unrecognized keys
- [x] 2.3 Create the `seed-loader` identity via `get_or_create`: `auth.User(username="seed-loader", is_staff=False)` and `LTIProfile(anon_id="seed-loader", scope="seed")`
- [x] 2.4 Import `LTICourse` records using `update_or_create(course_id=..., defaults=...)`
- [x] 2.5 Import `TargetObject` records using `update_or_create(pk=..., defaults=...)`; set `target_creator` to the `seed-loader` profile
- [x] 2.6 Import `Assignment` records using `update_or_create(assignment_id=..., defaults=...)`, resolving the `course` FK by `course_id`
- [x] 2.7 Import `AssignmentTargets` records using `update_or_create(assignment=..., target_object=..., defaults=...)`
- [x] 2.8 Set `TargetObject.target_courses` M2M after all courses exist
- [x] 2.9 Print JSON summary to stdout: `{ "created": {...}, "updated": {...}, "warnings": [...] }` with per-model counts

## 3. Tests

- [x] 3.1 Write a test that exports a course with assignments and target objects; assert the JSON structure and that excluded records (`course_users`, `LTIResourceLinkConfig`, profiles, users) are absent
- [x] 3.2 Write a test that exports a `TargetObject` shared by two courses; assert it appears exactly once in the output and `target_courses` contains only the exported courses
- [x] 3.3 Write a test that imports the exported JSON into a fresh DB; assert all records are created with correct FK and M2M relationships, and that `TargetObject.target_creator` points to the `seed-loader` profile
- [x] 3.4 Write a test for idempotency: import the same file twice; assert record counts do not change on the second run
- [x] 3.5 Write a test for unknown field handling: add a spurious key to a record in the JSON; assert import completes without error
