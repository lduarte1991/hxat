# Seeding a Development or Staging Database

Two Django management commands — `exportcourse` and `importcourse` — let you capture a representative set of courses from one environment and replay them into another. This is the recommended way to seed a fresh development or staging database.

## Overview

| Step | Command | What it does |
|------|---------|--------------|
| 1 | `exportcourse` | Reads courses from the source DB and writes a JSON seed file |
| 2 | `importcourse` | Reads the JSON seed file and upserts all records into the target DB |

The seed file is a plain JSON document (not a Django fixture) and is safe to version-control. Re-running `importcourse` on an existing database is idempotent.

---

## Step 1: Export courses

```bash
# Export a single course
python manage.py exportcourse --course-id <course_id> --output seed.json

# Export multiple courses listed in a JSON file (list of course ID strings)
python manage.py exportcourse --input-json courses2export.json --output seed.json
```

The seed file captures the full dependency graph for each course:
- `LTICourse` records
- `Assignment` and `AssignmentTargets` records (including annotation-database credentials)
- `TargetObject` records and their `target_courses` M2M links

`LTIProfile`, `auth.User`, and `LTIResourceLinkConfig` records are **not** exported.

### Preparing the course list file

`courses2export.json` is a JSON array of course ID strings:

```json
["course-id-1", "course-id-2", "course-id-3"]
```

---

## Step 2: Import into a target environment

```bash
python manage.py importcourse --input-json seed.json
```

This creates a fixed `seed-loader` identity (`auth.User` + `LTIProfile`) used as `target_creator` for all imported `TargetObject` records. All other records are upserted using natural keys, so re-running the same import is safe.

### Override annotation-database credentials

The seed file contains the annotation-database credentials from the source environment. When importing into a dev or staging environment you almost certainly want to point assignments at a local catchpy instance instead:

```bash
python manage.py importcourse \
    --input-json seed.json \
    --annox-db-url http://localhost:9000/annos \
    --annox-db-key consumer \
    --annox-db-secret secret
```

All three flags are optional and independent — supply only the ones you need to override. If a flag is omitted, the value from the seed file is used unchanged.

Typical values for a local docker-compose setup:

| Flag | Env var equivalent | Default docker value |
|------|--------------------|----------------------|
| `--annox-db-url` | `ANNOTATION_DB_URL` | `http://localhost:9000/annos` |
| `--annox-db-key` | `ANNOTATION_DB_KEY` | `consumer` |
| `--annox-db-secret` | `ANNOTATION_DB_SECRET` | `secret` |

### Add an admin user to every imported course

Imported courses have no `course_admins` by default. Use `--admin-profile-name` to attach an admin profile so the courses are immediately accessible through the hxat admin interface:

```bash
python manage.py importcourse \
    --input-json seed.json \
    --annox-db-url http://localhost:9000/annos \
    --annox-db-key consumer \
    --annox-db-secret secret \
    --admin-profile-name dev-admin
```

If the named `auth.User` and `LTIProfile` do not yet exist they are created automatically. If a user with that username already exists, it is reused.

---

## Typical dev workflow

```bash
# 1. On the source environment: export the courses you want
python manage.py exportcourse --input-json courses2export.json --output seed.json

# 2. On the target dev environment: import with local credentials
python manage.py importcourse \
    --input-json seed.json \
    --annox-db-url "$ANNOTATION_DB_URL" \
    --annox-db-key "$ANNOTATION_DB_KEY" \
    --annox-db-secret "$ANNOTATION_DB_SECRET" \
    --admin-profile-name dev-admin
```

Both commands print a JSON summary to stdout on success, and warnings (e.g. missing courses) to stderr.


## Sample hxat seed

A sample seed with already user and annotation database replace can be found in
`./artifacts/hxatseed-export.json`. The user has `anon_id == "harvardx` and annotation
database `(url, apikey, secret_token)` = (`http://localhost:8000/anno`, `consumer`,
`secret`).
