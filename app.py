from datetime import datetime, timedelta

import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

conn = st.connection("gsheets", type=GSheetsConnection)


def load_data():
    try:
        df = conn.read(usecols=[0, 1, 2], ttl=0)
        df = df.dropna(how="all")

        signups = {}
        for _, row in df.iterrows():
            key = f"{row['Date']} - {row['Role']}"
            signups[key] = row["Name"]
        return signups
    except Exception:
        return {}


def save_data(signups):
    schedule_list = []
    for key, name in signups.items():
        date, role = key.split(" - ")
        schedule_list.append({"Date": date, "Role": role, "Name": name})

    df = pd.DataFrame(schedule_list)
    conn.update(data=df)


# --- UI Setup ---
st.set_page_config(page_title="Ward Council Sign-ups", page_icon="📅")
st.title("Ward Council Assignments")
st.write("Welcome! Please claim an upcoming date.")

# --- Data Definition ---
# Automatically generate the next 4 Sundays
today = datetime.today()
next_sunday = today + timedelta(days=(6 - today.weekday()))
upcoming_sundays = [
    (next_sunday + timedelta(days=7 * i)).strftime("%b %d, %Y") for i in range(4)
]

roles = ["Spiritual Thought", "Handbook Training"]

# Load existing signups
signups = load_data()

# --- Sign-up Form ---
st.subheader("Sign Up Here")
with st.form("signup_form"):
    selected_date = st.selectbox("Select a Date", upcoming_sundays)
    selected_role = st.selectbox("Assignment", roles)

    # Text input for the user's name
    user_name = st.text_input("First and Last Name")

    submitted = st.form_submit_button("Claim Assignment")

    if submitted:
        clean_user_name = user_name.strip()

        if not clean_user_name:
            st.error("Please enter your name before submitting!")
        else:
            assignment_key = f"{selected_date} - {selected_role}"

            # NEW: Check if this user is already signed up for ANYTHING on this date
            user_already_booked = False
            for existing_key, existing_name in signups.items():
                if (
                    selected_date in existing_key
                    and existing_name.lower() == clean_user_name.lower()
                ):
                    user_already_booked = True
                    break

            if assignment_key in signups:
                st.error(
                    f"Oops! {signups[assignment_key]} already claimed the {selected_role} on {selected_date}."
                )
            elif user_already_booked:
                # NEW: Block the submission if they already have an assignment that day
                st.error(
                    f"Hold on, {clean_user_name}! You are already scheduled for an assignment on {selected_date}. Leave some fun for the rest of the council! 😉"
                )
            else:
                signups[assignment_key] = clean_user_name
                save_data(signups)
                st.success(
                    f"Success! {clean_user_name} is scheduled for {selected_role} on {selected_date}."
                )
                # Clear the cached data so the display updates instantly
                st.cache_data.clear()

# --- Current Schedule Display ---
st.divider()
st.subheader("Upcoming Schedule")

if signups:
    schedule_list = []
    current_date = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)

    for key, name in signups.items():
        date_str, role = key.split(" - ")
        assignment_date = datetime.strptime(date_str, "%b %d, %Y")

        if assignment_date >= current_date:
            schedule_list.append({"Date": date_str, "Role": role, "Name": name})

    if schedule_list:
        # NEW: Convert to a DataFrame and sort chronologically before displaying
        display_df = pd.DataFrame(schedule_list)

        # Create a temporary column with actual datetime objects for accurate sorting
        display_df["SortDate"] = pd.to_datetime(display_df["Date"], format="%b %d, %Y")

        # Sort by the new column, then drop it so it doesn't show in the UI
        display_df = display_df.sort_values(by="SortDate").drop(columns=["SortDate"])

        st.dataframe(display_df, width="stretch", hide_index=True)
    else:
        st.info("No upcoming assignments claimed yet.")
else:
    st.info("No assignments claimed yet. Be the first!")
