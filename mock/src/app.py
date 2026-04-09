import streamlit as st
from datetime import date, timedelta
import pandas as pd

WORK_DAYS = ["MON", "TUE", "WED", "THU", "FRI"]
DAY_LABELS = {
    "MON": "Monday",
    "TUE": "Tuesday",
    "WED": "Wednesday",
    "THU": "Thursday",
    "FRI": "Friday",
}


def main():
    ensure_mock_data()
    current_user_id = 1
    current_approver_id = 99

    st.title("Timesheet Dashboard")
    st.write("Overview of user and approver actions using mock timesheet data.")

    timesheets = st.session_state["mock_timesheet"]
    user_timesheets = [
        timesheet for timesheet in timesheets if timesheet["userID"] == current_user_id
    ]
    approver_timesheets = [
        timesheet
        for timesheet in timesheets
        if timesheet["approverID"] == current_approver_id
    ]

    user_notifications = []
    for timesheet in user_timesheets:
        status = timesheet["status"]
        if status == "Submitted":
            message = "Submitted and waiting for approval."
            action_label = "View"
        elif status == "Approved":
            message = "Approved and ready to review."
            action_label = "View"
        elif status == "Rejected":
            message = "Rejected. Please update and resubmit."
            action_label = "Edit"
        elif status == "In Progress":
            message = "Still in progress. Finish and submit when ready."
            action_label = "Edit"
        else:
            message = f"Current status: {status}"
            action_label = "View"
        user_notifications.append(
            {
                "timesheet": timesheet,
                "message": message,
                "action_label": action_label,
            }
        )

    approver_notifications = []
    for timesheet in approver_timesheets:
        if timesheet["status"] == "Submitted":
            approver_notifications.append(
                f"New submission from user {timesheet['userID']} for {timesheet['periodStart']} to {timesheet['periodEnd']}."
            )
        elif timesheet["status"] == "Resubmitted":
            approver_notifications.append(
                f"Resubmission received from user {timesheet['userID']} for {timesheet['periodStart']} to {timesheet['periodEnd']}."
            )
    if not any("Resubmission" in notification for notification in approver_notifications):
        approver_notifications.append(
            "Resubmission received from user 7 for 2024-01-15 to 2024-01-21."
        )

    pending_reviews = sum(
        1
        for timesheet in approver_timesheets
        if timesheet["status"] in {"Submitted", "Resubmitted"}
    )
    has_own_approver_assignment = any(
        timesheet["approverID"] == current_approver_id and timesheet["userID"] == current_user_id
        for timesheet in timesheets
    )

    user_col, approver_col = st.columns(2)

    with user_col:
        st.subheader("User Notifications")
        if not user_notifications:
            st.success("No user notifications right now.")
        for notification in user_notifications:
            timesheet = notification["timesheet"]
            st.info(
                f"Timesheet {timesheet['timesheet_id']} for {timesheet['periodStart']} to {timesheet['periodEnd']}: {notification['message']}"
            )
            action_col, secondary_col = st.columns(2)
            action_col.button(
                "View",
                key=f"user_view_primary_{timesheet['timesheet_id']}",
            )
            secondary_col.button(
                "Edit",
                key=f"user_edit_{timesheet['timesheet_id']}",
            )

    with approver_col:
        st.subheader("Approver Dashboard")
        metric_col, reminder_col = st.columns(2)
        metric_col.metric("Timesheets Left To Review", pending_reviews)
        if has_own_approver_assignment:
            reminder_col.warning("You also have a timesheet to submit.")
        else:
            reminder_col.success("No personal submission reminder.")

        st.write("Approver Notifications")
        if approver_notifications:
            for index, notification in enumerate(approver_notifications):
                st.warning(notification)
                review_col, details_col = st.columns(2)
                review_col.button("Review", key=f"review_{index}")
                details_col.button("View", key=f"approver_view_{index}")
        else:
            st.success("No new submissions or resubmissions to review.")

def ensure_mock_data():
    current_approver_id = 99
    if "mock_timesheet" not in st.session_state:
        st.session_state["mock_timesheet"] = [
            {"timesheet_id": 1, "userID": 1, "approverID": current_approver_id, "periodStart": date(2024, 1, 1), "periodEnd": date(2024, 1, 7), "status": "In Progress"},
            {"timesheet_id": 2, "userID": 1, "approverID": current_approver_id, "periodStart": date(2024, 1, 8), "periodEnd": date(2024, 1, 14), "status": "Submitted"}
        ]
    else:
        for timesheet in st.session_state["mock_timesheet"]:
            timesheet.setdefault("approverID", current_approver_id)
    if "mock_timeentries" not in st.session_state:
        st.session_state["mock_timeentries"] = [
            {
                "timeEntryID": 1,
                "timesheetID": 1,
                "userID": 1,
                "projectID": "130",
                "workDate": "MON",
                "duration": 8.0,
                "billingType": "billable",
                "notes": "Initial project planning and setup",
            },
            {
                "timeEntryID": 2,
                "timesheetID": 1,
                "userID": 1,
                "projectID": "200",
                "workDate": "TUE",
                "duration": 6.5,
                "billingType": "internal",
                "notes": "Team sync and internal documentation",
            },
            {
                "timeEntryID": 3,
                "timesheetID": 1,
                "userID": 1,
                "projectID": "130",
                "workDate": "FRI",
                "duration": 7.5,
                "billingType": "non-billable",
                "notes": "Bug fixes and support follow-up",
            },
            {
                "timeEntryID": 4,
                "timesheetID": 2,
                "userID": 1,
                "projectID": "130",
                "workDate": "MON",
                "duration": 3.5,
                "billingType": "billable",
                "notes": "Continued development and feature implementation",
            },
            {
                "timeEntryID": 5,
                "timesheetID": 2,
                "userID": 1,
                "projectID": "200",
                "workDate": "WED",
                "duration": 4.0,
                "billingType": "internal",
                "notes": "Client meeting and project review",
            },
        ]


def build_editable_timesheet_dataframe(timesheet_id):
    df = pd.DataFrame(columns=["Code", *WORK_DAYS]).set_index("Code")
    for entry in st.session_state["mock_timeentries"]:
        if entry["timesheetID"] != timesheet_id:
            continue
        code = entry["projectID"]
        if code not in df.index:
            df.loc[code] = [0.0] * len(WORK_DAYS)
        df.loc[code, entry["workDate"]] = float(entry["duration"])
    return df


def normalize_draft_dataframe(df):
    working_df = df.copy() if df is not None else pd.DataFrame()
    if "Code" in working_df.columns:
        working_df = working_df.set_index("Code")

    if working_df.empty:
        empty_df = pd.DataFrame(columns=WORK_DAYS)
        empty_df.index.name = "Code"
        return empty_df

    for day in WORK_DAYS:
        if day not in working_df.columns:
            working_df[day] = 0.0
    working_df = working_df[WORK_DAYS]

    aggregated_rows = {}
    for code, row in working_df.iterrows():
        clean_code = str(code).strip()
        if clean_code in {"", "nan", "None", "Total"}:
            continue
        day_values = {}
        total = 0.0
        for day in WORK_DAYS:
            duration = row.get(day, 0)
            duration = 0.0 if pd.isna(duration) else float(duration)
            duration = max(duration, 0.0)
            day_values[day] = duration
            total += duration
        if total <= 0:
            continue
        if clean_code not in aggregated_rows:
            aggregated_rows[clean_code] = {day: 0.0 for day in WORK_DAYS}
        for day in WORK_DAYS:
            aggregated_rows[clean_code][day] += day_values[day]

    normalized_df = pd.DataFrame.from_dict(aggregated_rows, orient="index")
    normalized_df = normalized_df.reindex(columns=WORK_DAYS, fill_value=0.0)
    normalized_df.index.name = "Code"
    return normalized_df


def get_timesheet_draft_key(timesheet_id):
    return f"timesheet_draft_{timesheet_id}"


def get_desktop_editor_key(timesheet_id):
    return f"desktop_editor_{timesheet_id}"


def get_mobile_editor_key(timesheet_id, day):
    return f"mobile_editor_{timesheet_id}_{day}"


def get_timesheet_layout_tracker_key(timesheet_id):
    return f"timesheet_layout_tracker_{timesheet_id}"


def get_or_create_timesheet_draft(timesheet_id):
    draft_key = get_timesheet_draft_key(timesheet_id)
    if draft_key not in st.session_state:
        st.session_state[draft_key] = normalize_draft_dataframe(
            build_editable_timesheet_dataframe(timesheet_id)
        )
    return st.session_state[draft_key].copy()


def set_timesheet_draft(timesheet_id, df):
    normalized_df = normalize_draft_dataframe(df)
    st.session_state[get_timesheet_draft_key(timesheet_id)] = normalized_df
    return normalized_df.copy()


def clear_editor_state_for_layout(timesheet_id, layout_mode):
    if layout_mode == "Desktop":
        st.session_state.pop(get_desktop_editor_key(timesheet_id), None)
        return

    for day in WORK_DAYS:
        st.session_state.pop(get_mobile_editor_key(timesheet_id, day), None)


def clear_timesheet_draft_state(timesheet_id):
    st.session_state.pop(get_timesheet_draft_key(timesheet_id), None)
    st.session_state.pop(get_desktop_editor_key(timesheet_id), None)
    st.session_state.pop(get_timesheet_layout_tracker_key(timesheet_id), None)
    for day in WORK_DAYS:
        st.session_state.pop(get_mobile_editor_key(timesheet_id, day), None)


def build_mobile_day_frames(df):
    day_frames = {}
    for day in WORK_DAYS:
        rows = []
        for code in df.index:
            duration = float(df.loc[code, day])
            if duration > 0:
                rows.append({"Project ID": code, "Hours": duration})
        day_frames[day] = pd.DataFrame(rows, columns=["Project ID", "Hours"])
    return day_frames


def apply_mobile_mock_styles():
    st.markdown(
        """
        <style>
        div[data-testid="stExpander"] {
            border: 3px solid #111111;
            border-radius: 0;
            margin-bottom: 0.9rem;
            overflow: hidden;
            box-shadow: none;
        }

        div[data-testid="stExpander"] details {
            border: none;
        }

        div[data-testid="stExpander"] summary {
            position: relative;
            min-height: 4.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 0 4.5rem 0 1rem;
        }

        div[data-testid="stExpander"] summary p {
            width: 100%;
            text-align: center;
            font-size: 1.35rem;
            font-weight: 600;
            color: #111111;
        }

        div[data-testid="stExpander"] summary svg {
            display: none;
        }

        div[data-testid="stExpander"] summary::after {
            content: "\\25BE";
            position: absolute;
            right: 1rem;
            width: 2.5rem;
            height: 2.5rem;
            border: 3px solid #111111;
            border-radius: 999px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
            background: #ffffff;
        }

        div[data-testid="stExpander"] details[open] summary::after {
            content: "\\25B4";
        }

        div[data-testid="stExpander"] details[open] summary {
            border-bottom: 3px solid #111111;
        }

        .mobile-day-total {
            text-align: right;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_mobile_timesheet_breakdown(df):
    day_frames = build_mobile_day_frames(df)
    week_total = 0.0
    for day in WORK_DAYS:
        week_total += day_frames[day]["Hours"].sum() if not day_frames[day].empty else 0.0
    st.metric("Week Total", f"{week_total:.1f}h")

    for day in WORK_DAYS:
        day_total = day_frames[day]["Hours"].sum() if not day_frames[day].empty else 0.0
        with st.expander(
            f"{DAY_LABELS[day]} ({float(day_total):.1f}h)",
            expanded=day == "WED" and day_total > 0,
        ):
            st.markdown(
                f"<div class='mobile-day-total'>Total hours: {float(day_total):.1f}</div>",
                unsafe_allow_html=True,
            )
            if day_frames[day].empty:
                st.caption("No entries recorded for this day.")
                continue

            display_day_df = day_frames[day].rename(
                columns={"Project ID": "Project / Activity"}
            )
            st.dataframe(
                display_day_df,
                hide_index=True,
                use_container_width=True,
            )


def render_mobile_readonly_timesheet(timesheet, include_user=False):
    st.write(f"Timesheet ID: {timesheet['timesheet_id']}")
    if include_user:
        st.write(f"User ID: {timesheet['userID']}")
    st.write(f"Period: {timesheet['periodStart']} to {timesheet['periodEnd']}")
    st.write(f"Status: {timesheet['status']}")
    render_mobile_timesheet_breakdown(
        build_editable_timesheet_dataframe(timesheet["timesheet_id"])
    )


def build_draft_dataframe_from_mobile_frames(day_frames):
    draft_rows = {}
    for day, frame in day_frames.items():
        for _, row in frame.iterrows():
            clean_code = str(row.get("Project ID", "")).strip()
            duration = row.get("Hours", 0)
            duration = 0.0 if pd.isna(duration) else float(duration)
            duration = max(duration, 0.0)
            if not clean_code or clean_code.lower() == "nan" or duration <= 0:
                continue
            if clean_code not in draft_rows:
                draft_rows[clean_code] = {work_day: 0.0 for work_day in WORK_DAYS}
            draft_rows[clean_code][day] += duration

    draft_df = pd.DataFrame.from_dict(draft_rows, orient="index")
    draft_df = draft_df.reindex(columns=WORK_DAYS, fill_value=0.0)
    draft_df.index.name = "Code"
    return draft_df


def save_timesheet_entries(timesheet, draft_df):
    remaining_entries = [
        entry
        for entry in st.session_state["mock_timeentries"]
        if entry["timesheetID"] != timesheet["timesheet_id"]
    ]
    next_entry_id = max(
        (entry["timeEntryID"] for entry in remaining_entries),
        default=0,
    ) + 1

    normalized_df = normalize_draft_dataframe(draft_df)
    for project_id, row in normalized_df.iterrows():
        for work_day in WORK_DAYS:
            duration = float(row[work_day])
            if duration <= 0:
                continue
            remaining_entries.append(
                {
                    "timeEntryID": next_entry_id,
                    "timesheetID": timesheet["timesheet_id"],
                    "userID": timesheet["userID"],
                    "projectID": project_id,
                    "workDate": work_day,
                    "duration": duration,
                    "billingType": "billable",
                    "notes": "",
                }
            )
            next_entry_id += 1

    st.session_state["mock_timeentries"] = remaining_entries
    timesheet["status"] = "Submitted"
    clear_timesheet_draft_state(timesheet["timesheet_id"])


def render_desktop_timesheet_editor(timesheet):
    draft_df = get_or_create_timesheet_draft(timesheet["timesheet_id"])
    display_df = draft_df.copy()
    if display_df.empty:
        display_df.loc[""] = [0.0] * len(WORK_DAYS)

    st.caption("Desktop view uses a weekly table layout.")
    edited_df = st.data_editor(
        display_df,
        num_rows="dynamic",
        key=get_desktop_editor_key(timesheet["timesheet_id"]),
    )

    normalized_df = set_timesheet_draft(timesheet["timesheet_id"], edited_df)
    totals = (
        normalized_df.sum().reindex(WORK_DAYS, fill_value=0.0)
        if not normalized_df.empty
        else pd.Series([0.0] * len(WORK_DAYS), index=WORK_DAYS)
    )
    st.dataframe(pd.DataFrame([totals], index=["Total"]))
    return normalized_df


def render_mobile_timesheet_editor(timesheet):
    apply_mobile_mock_styles()
    st.caption("Mobile view uses expandable day cards with a simple project and hours table.")
    base_df = get_or_create_timesheet_draft(timesheet["timesheet_id"])
    day_frames = build_mobile_day_frames(base_df)
    total_hours = 0.0
    for day in WORK_DAYS:
        total_hours += day_frames[day]["Hours"].sum() if not day_frames[day].empty else 0.0
    st.metric("Week Total", f"{total_hours:.1f}h")

    edited_day_frames = {}
    for day in WORK_DAYS:
        day_total = day_frames[day]["Hours"].sum() if not day_frames[day].empty else 0.0
        with st.expander(
            f"{DAY_LABELS[day]} ({float(day_total):.1f}h)",
            expanded=day == "WED",
        ):
            st.markdown(
                f"<div class='mobile-day-total'>Total hours: {float(day_total):.1f}</div>",
                unsafe_allow_html=True,
            )
            default_day_df = day_frames[day]
            if default_day_df.empty:
                default_day_df = pd.DataFrame(columns=["Project / Activity", "Hours"])
            else:
                default_day_df = default_day_df.rename(columns={"Project ID": "Project / Activity"})
            edited_day_frames[day] = st.data_editor(
                default_day_df,
                num_rows="dynamic",
                hide_index=True,
                key=get_mobile_editor_key(timesheet["timesheet_id"], day),
                column_config={
                    "Project / Activity": st.column_config.TextColumn("PROJECT / ACTIVITY"),
                    "Hours": st.column_config.NumberColumn("Hours", min_value=0.0, step=0.5),
                },
            )

            if "Project / Activity" in edited_day_frames[day]:
                edited_day_frames[day] = edited_day_frames[day].rename(
                    columns={"Project / Activity": "Project ID"}
                )

            updated_day_total = (
                edited_day_frames[day]["Hours"].fillna(0).sum()
                if "Hours" in edited_day_frames[day]
                else 0.0
            )
            st.caption(f"{DAY_LABELS[day]} total: {float(updated_day_total):.1f}h")

    normalized_df = set_timesheet_draft(
        timesheet["timesheet_id"],
        build_draft_dataframe_from_mobile_frames(edited_day_frames),
    )
    updated_total = float(normalized_df.sum().sum()) if not normalized_df.empty else 0.0
    st.caption(f"Current weekly total: {updated_total:.1f}h")
    return normalized_df


def createTimesheet():
    ensure_mock_data()

    timesheet = st.session_state["mock_timesheet"][0]
    st.subheader("Create Timesheet")
    details_col, status_col = st.columns(2)
    details_col.write(f"Timesheet ID: {timesheet['timesheet_id']}")
    details_col.write(f"User ID: {timesheet['userID']}")
    details_col.write(f"Period: {timesheet['periodStart']} to {timesheet['periodEnd']}")
    status_col.write(f"Status: {timesheet['status']}")

    layout_mode = st.radio(
        "Preview layout",
        ["Desktop", "Mobile"],
        horizontal=True,
        key=f"layout_mode_{timesheet['timesheet_id']}",
    )

    layout_tracker_key = get_timesheet_layout_tracker_key(timesheet["timesheet_id"])
    previous_layout = st.session_state.get(layout_tracker_key)
    if previous_layout != layout_mode:
        clear_editor_state_for_layout(timesheet["timesheet_id"], layout_mode)
        st.session_state[layout_tracker_key] = layout_mode

    if layout_mode == "Desktop":
        render_desktop_timesheet_editor(timesheet)
    else:
        render_mobile_timesheet_editor(timesheet)

    if st.button("Submit for Review"):
        save_timesheet_entries(
            timesheet,
            get_or_create_timesheet_draft(timesheet["timesheet_id"]),
        )
        st.success("Timesheet submitted for review.")
        st.rerun()

def viewTimesheet():
    ensure_mock_data()
    st.write("Completed timesheets:")
    layout_mode = st.radio(
        "Preview layout",
        ["Desktop", "Mobile"],
        horizontal=True,
        key="view_timesheet_layout_mode",
    )
    if layout_mode == "Mobile":
        apply_mobile_mock_styles()

    results = 0
    for timesheet in st.session_state["mock_timesheet"]:
        if timesheet["status"] in ["Submitted", "Approved", "Rejected"]:
            results += 1
            if results > 1:
                st.divider()
            if layout_mode == "Desktop":
                st.write(f"Timesheet ID: {timesheet['timesheet_id']} - Period: {timesheet['periodStart']} to {timesheet['periodEnd']} - Status: {timesheet['status']}")
                df = build_editable_timesheet_dataframe(timesheet["timesheet_id"])
                if df.empty:
                    df.loc["Total"] = [0.0] * len(WORK_DAYS)
                else:
                    df.loc["Total"] = df.sum()
                st.dataframe(df)
            else:
                render_mobile_readonly_timesheet(timesheet)
    if results == 0:
        st.write("No submitted timesheets found.")

def build_timesheet_dataframe(timesheet_id):
    df = build_editable_timesheet_dataframe(timesheet_id)
    if df.empty:
        df.loc["Total"] = [0.0] * len(WORK_DAYS)
    else:
        df.loc["Total"] = df.sum()
    return df


def approveTimesheet():
    ensure_mock_data()
    current_user_id = 99
    st.info("This is the approve timesheet page. In production it will only be visible to users with arrpoval access and will allow them to approve timesheets of users who have them as their approverID")
    layout_mode = st.radio(
        "Preview layout",
        ["Desktop", "Mobile"],
        horizontal=True,
        key="approve_timesheet_layout_mode",
    )

    pending_timesheets = [
        timesheet
        for timesheet in st.session_state["mock_timesheet"]
        if timesheet["status"] == "Submitted" and timesheet["approverID"] == current_user_id
    ]
    reviewed_timesheets = [
        timesheet
        for timesheet in st.session_state["mock_timesheet"]
        if timesheet["status"] in {"Approved", "Rejected"} and timesheet["approverID"] == current_user_id
    ]

    if layout_mode == "Desktop":
        pending_tab, reviewed_tab = st.tabs(["Pending Review", "Reviewed"])

        with pending_tab:
            if not pending_timesheets:
                st.write("No submitted timesheets awaiting your review.")
            for timesheet in pending_timesheets:
                st.write(f"Timesheet ID: {timesheet['timesheet_id']} - User: {timesheet['userID']} - Period: {timesheet['periodStart']} to {timesheet['periodEnd']}")
                st.dataframe(build_timesheet_dataframe(timesheet["timesheet_id"]))
                approve_col, reject_col = st.columns(2)
                if approve_col.button("Approve", key=f"approve_{timesheet['timesheet_id']}"):
                    timesheet["status"] = "Approved"
                    st.rerun()
                if reject_col.button("Reject", key=f"reject_{timesheet['timesheet_id']}"):
                    timesheet["status"] = "Rejected"
                    st.rerun()

        with reviewed_tab:
            if not reviewed_timesheets:
                st.write("No reviewed timesheets found.")
            for timesheet in reviewed_timesheets:
                st.write(f"Timesheet ID: {timesheet['timesheet_id']} - Status: {timesheet['status']} - Period: {timesheet['periodStart']} to {timesheet['periodEnd']}")
                st.dataframe(build_timesheet_dataframe(timesheet["timesheet_id"]))
        return

    apply_mobile_mock_styles()
    queue_mode = st.radio(
        "Approval queue",
        ["Pending Review", "Reviewed"],
        horizontal=True,
        key="approve_timesheet_mobile_queue",
    )

    target_timesheets = (
        pending_timesheets if queue_mode == "Pending Review" else reviewed_timesheets
    )
    if not target_timesheets:
        st.write(
            "No submitted timesheets awaiting your review."
            if queue_mode == "Pending Review"
            else "No reviewed timesheets found."
        )
        return

    for index, timesheet in enumerate(target_timesheets):
        if index > 0:
            st.divider()
        render_mobile_readonly_timesheet(timesheet, include_user=True)
        if queue_mode == "Pending Review":
            approve_col, reject_col = st.columns(2)
            if approve_col.button("Approve", key=f"approve_mobile_{timesheet['timesheet_id']}"):
                timesheet["status"] = "Approved"
                st.rerun()
            if reject_col.button("Reject", key=f"reject_mobile_{timesheet['timesheet_id']}"):
                timesheet["status"] = "Rejected"
                st.rerun()


# Main code for the app

pages = {
    "": [st.Page(main, title="Main")],
    "Timesheets":[
        st.Page(createTimesheet, title="Create Timesheet"),
        st.Page(viewTimesheet, title="View Timesheet"),
        st.Page(approveTimesheet, title="Approve Timesheet")
    ]
}

pg = st.navigation(pages)
pg.run()
