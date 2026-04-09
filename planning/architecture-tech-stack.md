# Architecture And Tech Stack

## Purpose

This document captures the implemented MVP architecture and current technology stack for the Django timesheet application. It is based on:

- the business requirements in [business-requirements.md](./business-requirements.md)
- the current Streamlit prototype in `mock/src/app.py`
- the current ERD in `planning/ERD/ERD v2/ERDv2.dbml`

The goal is to describe the current local Docker MVP in a way that is easy to reason about and still leaves a clean path for later enhancement beyond the hackathon prototype.

## Current MVP Status

The current application has been scaffolded and implemented as a local Django MVP in [`timesheet_platform/`](/c:/Users/ross.usher/Documents/Hackathon/timesheet_platform). It currently includes:

- username/password login with a seeded demo HR account
- HR user registration and profile maintenance
- HR project creation, assignment, and retirement
- employee timesheet create, edit, view, and batch submit flows
- approver review, approval, rejection, and resubmission handling
- persisted workflow events and notifications
- derived dashboard reminders
- local Docker bootstrap with SQLite

## Architecture Summary

The implemented MVP is a **Django modular monolith** with:

- **Django** as the main web framework
- **SQLite** as the current local Docker database
- **Django templates** for the current server-rendered UI
- **Custom CSS** for the current responsive styling
- **Django Admin** for MVP operational management
- **Django checks and scripted smoke tests** for current verification

This is preferred over a SPA architecture because the domain is strongly workflow-driven, form-heavy, role-based, and centered around relational data rather than highly interactive client-side state.

## Why Django

Django fits the problem well because the application needs:

- strong relational modelling
- built-in auth and permission support
- an admin interface for MVP setup and support
- rapid CRUD and workflow development
- server-rendered pages that can still feel dynamic
- a clean path from prototype to production

The existing Streamlit app is useful for validating workflows and layouts, but it is not a good long-term fit for:

- robust authentication and authorization
- admin-controlled configuration
- richer workflow history
- persistent notifications
- complex validation and approval logic
- maintainable production UI

## Recommended Tech Stack

### Core Application

- Python 3.12
- Django 5.2.13
- Django templates
- Custom CSS

Notes:

- the current implementation does not use HTMX or Tailwind
- those can still be introduced later if the UI becomes more interactive

### Data Layer

- SQLite for the current local Docker MVP
- optional PostgreSQL configuration is present in settings for later use, but it is not the active MVP database path
- Django ORM and migrations

### Auth And Access

- Custom Django user model from day one
- Django auth groups and permissions for Employee, Approver, and HR roles
- Django username/password authentication for MVP
- HR-managed registration of employee and approver accounts
- A seeded demo HR account created during local bootstrap so further demo accounts can be registered through the application
- Django Admin for user setup, approver assignment, and weekly contracted hours overrides
- HR-facing project management for creating and retiring project activity codes and assigning users to them

### Background Processing

- MVP: derive pinned reminders dynamically in application services at request time
- MVP: use scheduled Django management commands only for optional outbound delivery such as email digests or summary notifications
- Later if needed: Celery + Redis for higher-volume async processing

### Testing And Quality

- Django system checks
- Django migrations as schema verification
- scripted local smoke tests for workflow and permission validation

Later if needed:

- pytest
- pytest-django
- factory_boy
- coverage.py
- Playwright for a small number of end-to-end workflow tests

### Deployment

- MVP deployment should be a single Dockerized application deployment
- The Docker image should package the Django application and its runtime dependencies
- Additional hosting and infrastructure choices beyond Docker are out of scope for MVP
- run the application with a single configured business timezone for MVP, expected to be `Europe/London`, while storing timestamps in UTC

## Architectural Style

The system should be built as a **modular monolith**, not a microservice architecture.

Reasons:

- the domain is still evolving
- the team is small
- the workflows are tightly connected
- a single deployable unit is faster to build and easier to debug
- the admin and reporting needs are internal and relational

The monolith should still be structured into clear Django apps so boundaries remain understandable.

## Proposed Django App Structure

```text
timesheet_platform/
  config/
  apps/
    accounts/
    activities/
    timesheets/
    approvals/
    notifications/
    dashboards/
    audit/
  templates/
  static/
```

### `accounts`

Responsibilities:

- custom user model
- business unit
- approver relationship
- weekly contracted hours
- role flags and permission helpers
- login and session handling
- HR-facing user registration
- HR-facing user search and limited profile maintenance

### `activities`

Responsibilities:

- bookable codes currently represented as `Project` in the ERD
- user-to-activity assignment
- HR-facing project creation, assignment, and retirement screens for project category activity codes
- leave/activity metadata
- whether the activity is system-controlled for hours

### `timesheets`

Responsibilities:

- timesheet header records
- time entries
- weekly validation rules
- batch submission
- draft editing
- mobile and desktop entry views

### `approvals`

Responsibilities:

- approval queue
- approval and rejection actions
- rejection notes
- overdue review logic
- resubmission workflow handling

### `notifications`

Responsibilities:

- event notifications
- read/unread state
- delivery categories
- notification rendering support

### `dashboards`

Responsibilities:

- employee dashboard
- approver dashboard
- pinned reminder calculations
- filtered queue summaries

### `audit`

Responsibilities:

- workflow event history
- submission/approval/rejection/resubmission events
- actor tracking
- timestamped decision history

## UI Architecture

The UI is currently **server-rendered first** using Django templates and custom CSS.

This matches the prototype and the business requirements well:

- desktop timesheet entry uses a weekly table/grid
- submitted timesheet detail and approval review include mobile day-card presentation
- dashboard, people, and project screens are rendered as standard Django templates
- validation errors are returned through normal Django form rendering and message banners

### Current UI Pattern

- Django templates for full-page rendering
- a shared base template with role-based navigation
- responsive CSS for desktop and mobile layouts
- mobile day-card sections on read-only timesheet and approval review pages

HTMX is not currently part of the implementation.

### Desktop And Mobile

The business requirements and Streamlit prototype imply two distinct layouts:

- **Desktop**: weekly grid/table optimized for rapid entry
- **Mobile**: currently implemented as expandable Monday-Friday cards for read-only detail and approval review, while edit/create remains a responsive table layout

This keeps the current app usable on smaller screens while leaving room for a richer mobile entry editor later if needed.

## Domain Model And Data Design

## Current ERD Baseline

The current ERD defines these core entities:

- `User`
- `Project`
- `UserProject`
- `Timesheet`
- `TimeEntry`

This is a strong starting point, but it is missing several concepts now required by the business document:

- approver relationship
- weekly contracted hours per employee
- notification history
- pinned reminder logic
- workflow event history
- rejection note persistence
- resubmission tracking without a separate status

## Target Domain Model

### User

Recommended implementation:

- custom Django user model extending `AbstractUser`
- include:
  - `username`
  - `email` as optional or future-use contact field
  - `first_name`
  - `last_name`
  - `business_unit`
  - `weekly_contracted_hours`
  - `approver` as a nullable self-referencing foreign key

Rationale:

- avoids bolting workflow identity onto Django's default auth later
- supports MVP admin management cleanly
- captures the employee/approver relationship directly

Notes:

- `weekly_contracted_hours` should be the source field used for weekly validation rules
- HR users should be able to update `weekly_contracted_hours`, assigned approver, and user activity assignments without gaining timesheet workflow permissions
- for MVP, authentication should use Django's built-in username/password flow backed by hashed passwords in the database
- the conceptual `Role` and `UserRole` entities in the ERD currently map to Django auth groups and the built-in user-group membership tables rather than custom role models in code

### ActivityCode

The ERD currently uses `Project`, but the notes already indicate this is not a typical project.

Recommendation:

- keep the business concept but treat it as a **bookable activity code**
- implementation options:
  - keep the database table named `project`
  - or rename the Django model to something like `ActivityCode` and map to an existing table later if needed

Suggested fields:

- `code`
- `name`
- `category`
- `billing_type_default`
- `is_leave_code`
- `fixed_hours`
- `default_duration`
- `is_active`

This supports both:

- client/work/internal codes
- bank holiday
- annual leave
- sick leave

### UserActivityAssignment

Based on `UserProject` in the ERD.

Purpose:

- defines which codes a user is allowed to book against
- supports access control and validation
- all bookable activity codes, including leave codes, should be represented through assignment records
- leave codes may be assigned automatically by admin tooling or default provisioning rules rather than manually one-by-one
- HR users should be allowed to maintain these assignments through a limited profile-management interface
- HR users should also be able to assign users to a project from the project-management side, not only from the user-profile side

### Project Retirement

For MVP, deleting a project from the HR interface should be implemented as a **soft delete / retirement** for project-category activity codes:

- set `is_active` to false
- remove active user assignment rows for that project
- hide the retired project from future booking and HR active-project lists
- preserve historical `TimeEntry` rows that already reference the project

This keeps the user-facing delete behavior simple while protecting timesheet history.

### Timesheet

Suggested fields:

- `id`
- `user`
- `approver`
- `period_start`
- `period_end`
- `status`
- `submission_due_at`
- `approval_due_at`
- `submitted_at`
- `approved_at`
- `rejected_at`
- `is_submission_overdue`
- `is_approval_overdue`

Important design choice:

- store `approver` on the timesheet itself, even if a user also has a default approver
- enforce one timesheet per user per week with a database uniqueness constraint, ideally on `(user, period_start)`
- keep `approval_due_at` fixed to the original timesheet-period Friday cutoff for MVP, even when initial submissions or resubmissions arrive late

Reason:

- preserves approval responsibility historically
- avoids ambiguity if the employee's approver changes later
- keeps overdue review queue logic deterministic

### TimeEntry

Suggested fields:

- `id`
- `timesheet`
- `activity_code`
- `work_date`
- `duration`
- `billing_type`
- `notes`
- `entry_category`
- `system_controlled_hours`

Important design choice:

- in Django, do **not** duplicate `user_id` on `TimeEntry` unless a later performance case proves it necessary
- enforce a uniqueness constraint on `(timesheet, activity_code, work_date)` for MVP and merge duplicate UI rows at the service layer

Reason:

- the owning user is already available via `timesheet.user`
- this keeps the model cleaner than the current SQLite prototype schema

### WorkflowEvent

This is essential to support resubmission without introducing a separate `Resubmitted` status.

Suggested fields:

- `id`
- `timesheet`
- `event_type`
- `actor`
- `created_at`
- `comment`
- `metadata_json`

Suggested event types:

- `draft_created`
- `submitted`
- `approved`
- `rejected`
- `resubmitted`

Deterministic rule:

- when a submit action occurs after a prior `rejected` workflow event for the same timesheet, the system should record that submission as a resubmission in workflow history and notification content even though the main timesheet status returns to `Submitted`

### Notification

Recommended as a persisted event-notification model.

Suggested fields:

- `id`
- `recipient`
- `timesheet`
- `notification_type`
- `title`
- `body`
- `severity`
- `created_at`
- `read_at`

Important design choice:

- **pinned reminders should not be the primary persisted source of truth**

Instead:

- event notifications are persisted
- pinned reminders are derived from current timesheet state, due dates, workflow events, and user role

This keeps reminder behaviour aligned with live data and avoids stale reminder records.

## Status And Workflow Design

Per the business requirements, timesheets should use only these primary statuses:

- `In Progress`
- `Submitted`
- `Approved`
- `Rejected`

Resubmission should be represented by:

- a new `submitted` state after rejection
- a `WorkflowEvent` entry indicating it was a resubmission
- notification content that reflects the resubmission

This is cleaner than adding a separate `Resubmitted` status to the main state machine.

## Notification And Reminder Design

The business requirements distinguish two concepts:

- **notifications**
- **pinned reminders**

### Notifications

Persist these as explicit records for:

- timesheet submitted
- timesheet approved
- timesheet rejected
- resubmission received

### Pinned Reminders

Derive these from current state and dates for:

- employee reminder from Wednesday until submission
- employee overdue reminder from Friday until submission
- approver Friday review reminder
- approver overdue review reminder after Friday
- rejected timesheets still awaiting resubmission

Pinned reminder source-of-truth rule:

- pinned reminders are always derived from live timesheet state, workflow history, due dates, and current date in the business timezone
- they are not stored as independent durable records in MVP

### Why Derive Reminders

Derived reminders are preferable for MVP because:

- the rules are date-driven and state-driven
- the reminder text changes over time
- late submissions should remain in the overdue queue rather than restarting a deadline cycle
- the dashboard must always reflect the latest situation

### Timezone Handling

All reminder and deadline calculations should use a single configured business timezone and business-day calendar rather than server local time.

This matters because:

- Wednesday, Thursday, and Friday reminder transitions are date-sensitive
- overdue state must change consistently for all users
- tests need deterministic date-boundary behaviour

## Validation Design

Validation should live in a mix of:

- Django model constraints where simple and safe
- service-layer validation for workflow rules
- form validation for user-facing feedback

### Validation Rules For MVP

- one Monday-Friday timesheet per user per period
- batch submit only if every selected timesheet is valid
- validate weekly total against `expected_weekly_hours`
- include leave entries in the weekly total
- prevent manual override of fixed-hour leave codes
- restrict booking to assigned activity codes
- require rejection comment on reject action

## Approval Design

Approval functionality should be modeled as a dedicated application service rather than scattered across views.

Recommended service methods:

- `submit_timesheet(...)`
- `batch_submit_timesheets(...)`
- `approve_timesheet(...)`
- `reject_timesheet(...)`
- `resubmit_timesheet(...)`
- `build_employee_dashboard(...)`
- `build_approver_dashboard(...)`

This keeps workflow logic:

- testable
- reusable
- independent from the web layer

## Authorization Design

Recommended approach:

- all application access begins with authenticated login
- standard authenticated users can manage only their own timesheets
- approvers can review only timesheets where they are the assigned approver
- approvers still act as standard users for their own timesheets
- HR users can search user profiles and edit only approved profile-management fields such as weekly contracted hours, assigned approver, and assigned projects
- HR users can create project-category activity codes, assign users to them, and retire them from future use
- HR users can register new employee and approver accounts
- HR users must not create, edit, submit, approve, reject, or resubmit timesheets
- dashboard/menu separation is implemented in the UI, but enforced in the backend through permission checks

The system should not rely on UI hiding alone for security.

## Demo Account Bootstrap

For the local Docker MVP, the recommended approach is:

1. Run Django migrations during container startup.
2. Run a bootstrap management command after migrations.
3. Ensure a default demo HR account exists.
4. Log in with the demo HR account.
5. Use the HR screens to register a demo approver and a demo employee.

Important rule:

- the application must authenticate against Django user records stored in the database
- plain text demo credentials must never be used as the runtime authentication source

### Demo Credentials Storage

For this local-only MVP, it is acceptable to keep demo credentials in a plain text reference file such as `demo-credentials.txt`, provided that:

- it is used only as a local reference for demo usernames and passwords
- it is not treated as the source of truth for authentication
- Django still stores passwords as hashes in the database
- the file is kept local to the Docker project and should ideally be excluded from source control if it contains real demo passwords

If the team wants a committed template, a `demo-credentials.example.txt` file can be kept in source control while the real `demo-credentials.txt` remains local.

## Streamlit Prototype To Django Mapping

The current Streamlit app demonstrates:

- user dashboard notifications
- approver dashboard notifications
- desktop weekly entry
- mobile day-card entry
- mobile view for submitted timesheets
- mobile approval review

These should map into Django roughly as:

- Streamlit `main()` -> Django dashboard views and template partials
- Streamlit `createTimesheet()` -> timesheet create/edit views
- Streamlit `viewTimesheet()` -> submitted/history views
- Streamlit `approveTimesheet()` -> approval queue views
- HR prototype concepts -> Django people and project management views

The prototype should remain a reference for:

- workflow behaviour
- layout expectations
- demo-friendly interactions

It should not drive the production code structure directly, and the current Django MVP already diverges in a few places where a simpler server-rendered implementation was more practical.

## Suggested URL Structure

```text
/login/
/logout/
/dashboard/
/timesheets/
/timesheets/<id>/
/timesheets/<id>/edit/
/timesheets/batch-submit/
/approvals/
/approvals/<id>/
/approvals/<id>/approve/
/approvals/<id>/reject/
/people/
/people/search/
/people/create/
/people/<id>/
/projects/
/projects/create/
/projects/<id>/edit/
/projects/<id>/delete/
/notifications/
/admin/
```

## Suggested Template Structure

```text
templates/
  base.html
  dashboards/
  registration/
  activities/
  accounts/
  timesheets/
  approvals/
```

## Database Recommendation

### MVP

- SQLite for the current local Docker MVP
- Django migrations as the source of truth
- seed data/fixtures for demo users, activity codes, and example timesheets

Later if needed:

- PostgreSQL can be enabled as a follow-on database target

### Why Not Reuse The SQLite Prototype Schema Directly

The current SQLite schema is a good prototype baseline but should not be copied unchanged because:

- it does not contain approver linkage on timesheets
- it does not contain notification or workflow history entities
- it duplicates `userID` on `TimeEntry`
- it does not capture employee-specific weekly hour overrides
- it does not yet model reminder or rejection metadata fully

## Testing Strategy

### Unit Tests

Cover:

- validation logic
- due-date calculations
- timezone-boundary calculations for reminder transitions
- reminder generation
- approval workflow
- resubmission behaviour

### Integration Tests

Cover:

- create/edit/submit flow
- batch submit
- approve/reject/resubmit flow
- employee and approver dashboard contents
- reminder state transitions across dates
- fixed-hour leave behavior
- duplicate activity/day row merge behaviour

### End-To-End Tests

Cover:

- desktop weekly entry
- mobile day-card detail and approval review
- approval queue on desktop and mobile
- parity between desktop and mobile views for the same underlying timesheet data

### Time Control In Tests

Use explicit clock control for reminder and overdue tests.

Recommended approach:

- freeze time in unit, integration, and end-to-end scenarios where Wednesday, Thursday, and Friday transitions matter
- validate behaviour before due date, on due date, and after due date
- validate late initial submission and late resubmission against the original fixed `approval_due_at`

## Operational Admin Design

Use Django Admin in MVP for:

- user creation
- approver assignment
- weekly contracted hours override
- activity code maintenance
- user-to-activity assignments
- support inspection of workflow events and notifications

This matches the business requirement to keep MVP admin capability simple.

In addition to Django Admin, the MVP should provide a limited HR-facing application screen for:

- registering users
- searching users
- opening a user profile
- editing weekly contracted hours
- editing assigned approver
- editing assigned project or activity assignments
- creating project-category activity codes
- assigning users to new or existing projects
- retiring projects from future use while preserving historical time entries

## Key Risks And Tradeoffs

### Risk: Workflow Rules Spread Across Views

Mitigation:

- centralize domain logic in services

### Risk: Reminder Logic Becomes Fragile

Mitigation:

- derive reminders from state plus due dates
- cover reminder transitions with date-based tests

### Risk: ERD Drift From Real Requirements

Mitigation:

- treat the current ERD as a starting point
- update the ERD after the Django model design is agreed

### Risk: Frontend Complexity Grows

Mitigation:

- keep the UI server-rendered
- use HTMX only for focused interactions
- avoid a SPA unless product needs change materially

## Recommended Next Steps

1. Add a formal automated test suite around the implemented workflows.
2. Decide whether to keep SQLite for the next phase or move the Docker MVP to PostgreSQL.
3. Extend the mobile entry experience if the responsive table is not sufficient.
4. Add dependency auditing and final deployment hardening checks before any broader handoff.
