## Context

`importcourse` already creates a fixed synthetic identity (`seed-loader`) via `get_or_create` before importing any records. That pattern is reused here. The command uses `update_or_create` keyed on natural identifiers for all models; `course_admins` is a ManyToMany relation managed via `add()`.

See `proposal.md` — Why for motivation.

## Goals / Non-Goals

**Goals:**
- Add `--admin-profile-name` flag to `importcourse`
- Resolve or create an `auth.User` + `LTIProfile` pair for the supplied name before any records are imported
- Call `course.course_admins.add(profile)` for every course touched in the run

**Non-Goals:**
- No changes to `exportcourse` or the seed JSON format
- No validation that the named user has staff/superuser privileges — this is a seeding tool
- No support for multiple admin profiles in a single invocation

## Decisions

### Reuse the seed-loader get_or_create pattern
The existing code already does `get_or_create` for `seed-loader` in step 1 of `handle()`. The admin identity follows the same shape: `User(username=name)` + `LTIProfile(anon_id=name, scope=name, user=user)`. Using `scope=name` keeps it consistent with the seeding namespace and avoids collisions with real profiles whose `anon_id` might coincidentally match.

Alternative considered: require the user/profile to pre-exist and fail if not found. Rejected — requires an out-of-band setup step; auto-creation is more ergonomic for dev seeding and mirrors the seed-loader precedent.

### Add admin to course_admins after update_or_create
`course.course_admins.add(profile)` is idempotent on a ManyToMany, so it can be called unconditionally for every course without checking membership first. This keeps the code simple.

### Flag is optional with no default
Omitting `--admin-profile-name` leaves `course_admins` untouched. This is a backward-compatible addition — existing scripts need no changes.

## Risks / Trade-offs

- [Scope creep] The synthetic admin identity persists in the database after seeding. → Acceptable for a dev/staging tool; operators can delete it manually if needed.
- [Name collision] A real user with a username matching the supplied name will be found and reused as the admin profile. → Document this in the command's help text; it is intentional behaviour for cases where the real user already exists.
