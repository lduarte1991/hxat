## Purpose

Provides a management command that serializes a representative set of courses and their full dependency graph into a portable JSON seed file, suitable for loading into a development or staging database.

## Requirements

### Requirement: Accept course list input
The command SHALL accept course IDs either as a single `--course-id` argument or as a `--input-json` argument pointing to a JSON file containing a list of course ID strings.

#### Scenario: Single course ID
- **WHEN** the command is run with `--course-id <id>`
- **THEN** the graph for that one course is exported

#### Scenario: JSON file input
- **WHEN** the command is run with `--input-json <path>` pointing to a valid JSON file containing a list of course ID strings
- **THEN** the graphs for all listed courses are exported into a single output file

#### Scenario: No input provided
- **WHEN** the command is run without `--course-id` or `--input-json`
- **THEN** the command exits with an error message describing the missing input

### Requirement: Collect full course graph
For each course ID, the command SHALL collect and include in the export:
- The `LTICourse` record
- All `Assignment` records whose FK points to that course
- All `AssignmentTargets` records for those assignments
- All `TargetObject` records referenced by those `AssignmentTargets`

`LTIProfile` and `auth.User` records are NOT collected. Profiles are created automatically during LTI launch; they do not need to be seeded.

#### Scenario: Course with assignments and targets
- **WHEN** a course has assignments, each with one or more target objects
- **THEN** all assignments, assignment targets, and target objects appear in the export

#### Scenario: TargetObject shared across exported courses
- **WHEN** a `TargetObject` is referenced by assignments in two different exported courses
- **THEN** the object appears exactly once in the export

### Requirement: Exclude non-essential records
The command SHALL NOT include the following in the export:
- `LTIResourceLinkConfig` records (auto-created on LTI launch)
- `course_users` M2M entries (learner enrollment)
- `LTICourseAdmin` records (pending admin state)

#### Scenario: Course with learner enrollments
- **WHEN** a course has entries in `course_users`
- **THEN** those enrollment entries are absent from the export

### Requirement: Trim TargetObject cross-course M2M
The `target_courses` M2M on each exported `TargetObject` SHALL be trimmed in the output to reference only courses that are included in the same export.

#### Scenario: TargetObject linked to a non-exported course
- **WHEN** a `TargetObject` has a `target_courses` entry pointing to a course not in the export set
- **THEN** that course reference is absent from the serialized target object

### Requirement: Output format
The command SHALL write a single JSON file with the following top-level structure:
```
{
  "exported_at": "<ISO 8601 timestamp>",
  "courses": ["<course_id>", ...],
  "data": {
    "courses": [...],
    "target_objects": [...],
    "assignments": [...],
    "assignment_targets": [...]
  }
}
```
The output path SHALL be controlled by an `--output` argument; if omitted, the command SHALL write to stdout.

#### Scenario: Output to file
- **WHEN** `--output <path>` is provided
- **THEN** the JSON is written to that file and a summary is printed to stdout

#### Scenario: Output to stdout
- **WHEN** `--output` is not provided
- **THEN** the JSON is written to stdout

### Requirement: Missing course handling
The command SHALL report a warning for each course ID that is not found in the database and continue processing remaining IDs.

#### Scenario: One course ID not found
- **WHEN** one course ID in the input does not exist in the database
- **THEN** a warning is printed for that ID and all other courses are exported normally
