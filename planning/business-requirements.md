# Business Requirements

## Overview

This document captures the initial business requirements for the timesheet application. It is intended to be a working draft that can be reviewed, updated, and expanded as the product direction becomes clearer.

## Purpose

The system should allow users to create, submit, review, approve, reject, and resubmit timesheets in a simple and trackable way. It should also give approvers visibility of outstanding work and notify both users and approvers when action is needed. Users who are also approvers must have a clear separation between their personal timesheet workflow and their approval workflow.

## Goals

- Reduce manual effort in timesheet submission and approval.
- Make it clear what action each user needs to take.
- Provide approvers with a quick view of pending reviews and items still awaiting user resubmission.
- Support a basic workflow for in progress, submitted, approved, and rejected timesheets, while still supporting resubmission behaviour.
- Make the status of each timesheet and the next required action easy to understand.
- Support a usable experience on both desktop and mobile layouts.
- Make missed submission and approval deadlines visible so follow-up can happen quickly.
- Distinguish clearly between general notifications and pinned reminders for urgent action.

## In Scope

- Timesheet creation and editing by end users.
- Username and password login for registered users.
- Batch submission of multiple completed timesheets.
- Submission of timesheets for approval.
- Approval and rejection by assigned approvers.
- Resubmission of rejected timesheets.
- Rejection notes visible to the employee.
- Leave and non-project time entry for bank holidays, annual leave, and sick leave.
- Validation of weekly totals against expected working hours for MVP.
- Notifications for key workflow events.
- Reminder notifications for submission and approval deadlines.
- Flagging of missed deadlines on dashboards and notifications.
- Separate dashboard and menu areas for personal timesheet work and approval work.
- A simple dashboard for users and approvers.
- A mobile-friendly version of the web app with an alternate layout.
- Basic admin management of approver assignments for MVP.
- HR user search and maintenance of selected user profile fields.
- HR creation and retirement of projects together with user assignment management.
- HR-led registration of employee and approver user accounts.
- A seeded demo HR account for first-time local MVP setup.

## User Roles

### Employee

An employee can:

- Log in to the application with their registered account.
- Create and edit their own timesheet drafts.
- Create timesheets for Monday to Friday working weeks only.
- Enter project time and approved non-project time categories in their timesheet.
- Submit a timesheet draft for review.
- Batch submit multiple completed timesheets.
- View the status of submitted timesheets.
- Edit and resubmit a rejected timesheet.
- View rejection notes from the approver.

### Approver

An approver can:

- Log in to the application with their registered account.
- Review timesheets of users assigned to them.
- Approve or reject submitted timesheets.
- Add a rejection note that is visible to the employee.
- See how many timesheets are waiting for review and how many rejected timesheets are still waiting to be resubmitted by users.
- Receive notifications for new submissions and resubmissions.
- Chase up users when rejected timesheets have not yet been resubmitted.
- See missed employee submission deadlines for users assigned to them.
- See when their own approval deadlines have been missed.

An approver is also a normal user for their own timesheets. Their personal timesheet dashboard and menu options must remain separate from their approval dashboard and approval menu options so the two workflows are clearly distinguished.

### HR

An HR user can:

- Log in to the application with their registered account.
- Register new employee and approver user accounts.
- Search for employees and approvers in the system.
- Open a user profile and view core profile details.
- Edit selected profile fields including weekly contracted hours, assigned projects, and assigned approver.
- Create new projects and assign users to them.
- Retire projects and remove all user assignments from them.
- Manage user profile data without taking part in personal timesheet or approval workflows.

An HR user must not:

- Create, edit, submit, approve, reject, or resubmit timesheets.
- Access approval queues or employee timesheet workflow screens except where profile context is shown for administration.

## Core Workflow

1. An employee creates or updates a timesheet for a Monday to Friday week.
2. The employee can batch submit one or more completed weekly timesheets.
3. The employee should submit their timesheet by Thursday of that week.
4. A pinned reminder should appear for the employee from Wednesday and remain visible until submission.
5. If the employee has still not submitted by Friday, the reminder becomes an overdue reminder and the assigned approver can see the missed deadline on their dashboard.
6. The approver reviews submitted timesheets assigned to them.
7. The approver receives a notification as soon as a timesheet is pending approval.
8. The approver either approves the timesheet or rejects it with a visible rejection note.
9. If rejected, the employee updates and resubmits the timesheet.
10. The approver should complete approval, including any resubmissions, by Friday of that week.
11. On Friday, the approver dashboard should show a pinned reminder for the number of reviews due that day and this should convert to an overdue reminder after Friday until the approvals are completed.
12. If an initial submission or resubmission arrives late, it should remain in the overdue review reminder queue rather than creating a new deadline cycle for MVP.
13. Notifications, reminders, and dashboards reflect the latest action completed and the next action required.

## Functional Requirements

### Authentication And User Provisioning

- The system must require registered users to log in before accessing role-based application features.
- For MVP, the system must support username and password login.
- The system must allow HR users to register new employee and approver accounts.
- The HR registration flow must allow setup of the user's role, weekly contracted hours, assigned approver, and assigned projects.
- The local MVP setup must provide a seeded demo HR account so the first HR login can create further demo users.
- The seeded demo HR account must be able to create a demo approver and a demo employee account through the application.

### Project Management

- The system must allow HR users to create a project.
- The HR project creation flow must allow the HR user to assign one or more users to the new project.
- The system must allow HR users to remove users from a project.
- The system must allow HR users to retire a project so it is no longer available for future timesheet entry.
- When a project is retired, all active user-to-project assignments for that project must be removed.
- For MVP, project retirement should preserve historical timesheet data rather than deleting historical time entries.

### Timesheet Management

- The system must allow a user to create a timesheet for a defined period.
- The system must support Monday to Friday five-day weeks only for each individual timesheet.
- The system must allow a user to add, edit, and remove time entries in a timesheet.
- The system must store a status against each timesheet.
- The system must allow a user to submit a completed timesheet for approval.
- The system must allow a user to batch submit multiple completed timesheets.
- The system must allow a rejected timesheet to be edited and resubmitted.
- The system should support resubmission as workflow behaviour without requiring a separate `Resubmitted` status, provided the system still records and surfaces that a rejected timesheet has been submitted again.

### Leave And Non-Project Time

- The system must allow users to record bank holidays, annual leave, and sick leave in a timesheet.
- Bank holidays must be entered as a fixed full-day value of 7.5 hours.
- Sick leave must be entered as a fixed full-day value of 7.5 hours.
- Annual leave must support both half-day and full-day entries.
- For MVP, annual leave full day is 7.5 hours and half day is 3.75 hours.
- Users must not manually edit the fixed hours for bank holidays, annual leave, or sick leave entries.

### Validation And Submission Rules

- The system must only allow batch submission when every selected timesheet is complete and valid.
- The system must validate each weekly timesheet against expected working hours before submission.
- For MVP, expected working hours should default to 37.5 hours per week.
- Weekly contracted hours used for validation must be overrideable per employee.
- For MVP, the per-employee override may be maintained through an admin panel rather than a user-facing settings screen.
- Weekly validation should include project time together with approved leave or non-project time entries.

### Approval Workflow

- The system must assign each timesheet to an approver.
- The system must allow an approver to view submitted timesheets assigned to them.
- The system must allow an approver to approve a timesheet.
- The system must allow an approver to reject a timesheet.
- The system must require an approver to enter a note or reason when rejecting a timesheet.
- The rejection note must be visible to the employee.
- The system must allow a rejected timesheet to be edited and resubmitted.
- The system must distinguish between an approver's own personal timesheet actions and their approval actions for other users.
- The system must allow approvers to see rejected timesheets that are still awaiting user resubmission so they can chase them up if needed.
- The system must show approvers when assigned users have missed the Thursday submission deadline.
- The system must show approvers when their own Friday approval deadline has been missed.
- Missed Friday approval deadlines should be visible only to the approver responsible for that approval and should not be escalated to a further approver for MVP.
- If an initial submission or resubmission is already late, the item should stay within the overdue review reminder queue until completed rather than resetting the approval target.

### Notifications And Reminders

- The system must notify employees when a timesheet is submitted.
- The system must notify employees when a timesheet is approved.
- The system must notify employees when a timesheet is rejected.
- The system must notify approvers when a new timesheet is submitted to them.
- The system must notify approvers when a rejected timesheet has been resubmitted.
- The system must notify approvers when they also need to submit their own timesheet.
- The system must distinguish between standard notifications and pinned reminders.
- The system must show employees a pinned submission reminder from Wednesday until the timesheet is submitted.
- If the employee has not submitted by Friday, the employee reminder must convert into an overdue reminder and remain pinned until submission.
- The system must remind approvers to complete approvals, including resubmissions, by Friday of that week.
- The system must notify approvers immediately when a timesheet becomes pending review.
- The approver dashboard must show a pinned reminder on Friday summarising the number of reviews due that day.
- After Friday, the approver pinned reminder must convert into an overdue reminder and remain visible until all overdue approvals are completed.
- The system should highlight rejected timesheets that have not yet been resubmitted so approvers can chase them up if needed.
- The system must show a pinned overdue notification when an employee misses the Thursday submission deadline.
- The system must show missed employee submission deadlines on the relevant approver dashboard.
- The system must show missed Friday approval deadlines on the approver's own dashboard.

### Dashboard And Navigation

- The system must provide employees with a view of timesheet statuses and required actions.
- The system must provide approvers with a count of timesheets pending review.
- The system must provide approvers with notifications for new submissions and resubmissions.
- The system must provide separate areas for notification history and pinned reminders.
- The system must provide approvers with a view of rejected timesheets that are awaiting employee resubmission.
- The system must provide approvers with a view of missed employee submission deadlines.
- The approver dashboard should support filtering and sorting by user and due date for follow-up activity.
- The system must keep personal timesheet workflow areas separate from approval workflow areas in both menus and dashboards.
- The system must provide HR users with a user search screen and a user profile screen for profile maintenance.
- The system must provide HR users with a project management screen.
- HR navigation must be separate from employee and approver workflow navigation.
- HR users must not be shown timesheet entry or approval workflow menus.

### Mobile Experience

- The system must provide a mobile-friendly layout that differs from the desktop table layout.
- In mobile view, the timesheet experience should present Monday to Friday as separate expandable day sections or cards with the total hours for each day shown clearly.
- In mobile view, expanding a day should show a simple list or table of project ID and hours entries for that day.
- In mobile view, the user must be able to add and remove project time rows within the selected day.
- The mobile treatment should also be applied to viewing submitted timesheets and approver review screens, not just timesheet entry.

## Data Requirements

- A user record must support login credentials.
- A user record must store a username or other login identifier.
- A user record must store a password hash rather than plain text password storage in the application database.
- A user record must store the user's role or permission mapping.
- A user record should store whether the account is active.
- A timesheet must have an ID.
- A timesheet must be linked to a user.
- A timesheet must be linked to an approver.
- A timesheet must include a period start date and period end date.
- A timesheet must include a status.
- Supported statuses are `In Progress`, `Submitted`, `Approved`, and `Rejected`.
- The system must record whether a submitted timesheet is an initial submission or a resubmission through workflow history, notification metadata, or equivalent audit data.
- A timesheet should store submission, approval, and rejection timestamps to support deadline reminders and tracking.
- A timesheet should store submission and approval due dates.
- A timesheet should store whether a submission deadline or approval deadline has been missed.
- A rejected timesheet must store the rejection note or reason.
- An employee record should store weekly contracted hours used for timesheet validation.
- An employee record should store the assigned approver.
- User-to-project or user-to-activity assignments must be stored so HR can maintain assigned projects.
- A project or activity record should store whether it is active so retired projects can be hidden from future booking while preserving history.
- A time entry must be linked to a timesheet.
- A time entry should include project or code, work day/date, duration, and notes.
- A time entry should include a category or type so the system can distinguish between project work, bank holiday, annual leave, sick leave, and other future non-project types.
- Fixed leave-type entries should store whether the hours were system-controlled rather than manually entered.

## Non-Functional Requirements

- The interface should be simple and easy to understand.
- The system should make outstanding actions obvious.
- The initial version should support mock or demo data for prototyping.
- The design should be suitable for extension into a production workflow later.
- The desktop and mobile experiences should both be clear and usable for day-to-day entry and approval tasks.
- The mobile experience should prioritise readability and simple editing over dense table layouts.

## MVP Delivery Notes

- For MVP, administrative actions such as approver reassignment may be supported through a framework-provided admin interface rather than a bespoke user-facing screen.
- For MVP, authentication and user administration may rely on framework-provided capabilities if they meet the required business needs.
- For MVP, deleting a project in the HR interface may be implemented as a soft delete or retirement action that removes active assignments and future booking access while preserving historical timesheet records.
- In the current Django MVP implementation, submitted timesheet detail and approver review screens include mobile day-card presentation, while create and edit screens currently use a responsive table layout.
- For the local Docker MVP, a seeded demo HR account should be created during bootstrap if it does not already exist.
- For the local Docker MVP, demo usernames and passwords may be kept in a local `demo-credentials.txt` reference file for convenience.
- The `demo-credentials.txt` file should be treated as a local-only reference and should not be the application's authentication source.
- Actual authentication credentials must still be stored as password hashes in the application database.
- Post-MVP reporting may include rejection trends by user so approvers can identify recurring issues with particular employees.
- No additional post-MVP reporting or export requirements have been identified at this stage.

## Open Questions

No open questions are currently captured.
