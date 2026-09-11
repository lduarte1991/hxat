## 1. Update importcourse command

- [x] 1.1 Add `--admin-profile-name` optional argument to `add_arguments()` in `importcourse.py`
- [x] 1.2 At the start of `handle()`, if `--admin-profile-name` is supplied, use `get_or_create` to ensure `auth.User(username=name)` exists
- [x] 1.3 Use `get_or_create` to ensure `LTIProfile(anon_id=name, scope=name, user=user)` exists and capture the profile object
- [x] 1.4 Tally the admin `auth.User` and `LTIProfile` creation results in the existing `created`/`updated` counters

## 2. Wire admin profile into course import

- [x] 2.1 After each `LTICourse.objects.update_or_create(...)` call, if an admin profile is resolved, call `course.course_admins.add(admin_profile)`

## 3. Verify

- [x] 3.1 Manual smoke test: run `importcourse --input-json <seed> --admin-profile-name dev-admin` on an empty database and confirm the user, profile, and course admin memberships are created
- [x] 3.2 Re-run the same command and confirm it is idempotent (no duplicate entries, no errors)
- [x] 3.3 Run `importcourse --input-json <seed>` without the flag and confirm existing behaviour is unchanged
