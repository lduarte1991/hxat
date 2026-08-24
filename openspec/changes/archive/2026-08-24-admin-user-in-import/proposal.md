## Why

The `importcourse` command creates `LTICourse` records but never populates `course_admins`. Developers and operators seeding a staging or development environment need at least one admin attached to each course to be able to inspect or edit them.

## What Changes

- `importcourse` gains an optional `--admin-profile-name` flag. The final state for this
  admin user should be a `auth.User.username` == `admin_profile_name`, with an associated
  `LTIProfile.user_id` == `admin_profile_name` and `LTIProfile.anon_id` ==
  `admin_profile_name`. This profile should be added as admin for all courses created or
  updated during the import run
- If the `auth.User` or `LTIProfile` for `admin_profile_user` don't yet exist, the command creates one (same pattern as the existing `seed-loader` identity creation).
- The flag is optional; omitting it preserves the current behaviour (no `course_admins` set).

## Capabilities

### New Capabilities

- `course-import-admin`: Optionally associate a named admin user with every course during import.

### Modified Capabilities

- `course-import`: The `--admin-profile-name` flag extends the existing import command's behaviour; the natural-key upsert and summary requirements are unchanged.

## Impact

- Modified file: `utils/management/commands/importcourse.py`
- No migrations required
- No change to the export format or `exportcourse.py`
- No other commands or views affected
