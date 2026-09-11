## Context

`importcourse` builds `defaults` dicts for `Assignment.objects.update_or_create()` by passing the seed file fields through `_safe_defaults()`. The three credential fields (`annotation_database_url`, `annotation_database_apikey`, `annotation_database_secret_token`) are valid model fields so they pass through unchanged.

The override is a simple post-filter on those `defaults` dicts: if an override value was supplied, replace the corresponding key before the `update_or_create` call. No model changes, no migrations.

See `proposal.md` — Why for motivation.

## Goals / Non-Goals

**Goals:**
- Add `--annox-db-url`, `--annox-db-key`, `--annox-db-secret` flags to `importcourse`
- Apply each override to the `defaults` dict for every `Assignment` upsert in the run

**Non-Goals:**
- No per-assignment or per-course granularity — the override is global for the entire import run
- No reading from env vars automatically — the caller must pass the flags explicitly
- No changes to `exportcourse` or the seed JSON format

## Decisions

### Override by mutating the defaults dict before update_or_create
The existing flow builds a `defaults` dict per assignment from the seed data. Injecting the override values into that dict immediately before calling `update_or_create` keeps the change minimal and localised — the rest of the import loop is unchanged.

Alternative: strip credential fields from the seed entirely and always require the flags. Rejected — would be a breaking change for callers that intentionally carry credentials across environments.

### Three independent flags, not one combined flag
Each credential field is independent in the model; operators may need to override only the URL (e.g. same key/secret, different host). Three separate flags give maximum flexibility with minimal complexity.

### No automatic env-var fallback
Django management commands conventionally take explicit arguments rather than reading env vars silently. Callers who want env-var-driven behaviour can wrap the command in a shell script (`python manage.py importcourse ... --annox-db-url "$ANNOTATION_DB_URL"`).

## Risks / Trade-offs

- [Accidental omission] An operator who forgets the flags will import prod credentials into dev without any warning. → Document the flags prominently in the command's help text; consider adding a stderr warning when credential fields from the seed appear to be production URLs (future work, out of scope here).
