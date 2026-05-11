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
            key = f"{row["Date"]} - {row["Role"]}"
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

    # NEW: Text input for the user's name
    user_name = st.text_input("First and Last Name")

    submitted = st.form_submit_button("Claim Assignment")

    if submitted:
        # Check if they actually typed a name
        if not user_name.strip():
            st.error("Please enter your name before submitting!")
        else:
            # Create a unique key for the date+role to prevent double-booking
            assignment_key = f"{selected_date} - {selected_role}"

            if assignment_key in signups:
                st.error(
                    f"Oops! {signups[assignment_key]} already claimed the {selected_role} on {selected_date}."
                )
            else:
                signups[assignment_key] = user_name.strip()
                save_data(signups)
                st.success(
                    f"Success! {user_name} is scheduled for {selected_role} on {selected_date}."
                )

# --- Current Schedule Display ---
st.divider()
st.subheader("Upcoming Schedule")

if signups:
    schedule_list = []

    # Get today's date for comparison (reset to midnight so Sunday assignments show up on Sunday)
    current_date = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)

    for key, name in signups.items():
        date_str, role = key.split(" - ")

        # Convert the string date (e.g., "May 17, 2026") back into a Python datetime object
        assignment_date = datetime.strptime(date_str, "%b %d, %Y")

        # Only add it to the table if the assignment date is today or in the future
        if assignment_date >= current_date:
            schedule_list.append({"Date": date_str, "Role": role, "Name": name})

    if schedule_list:
        st.dataframe(schedule_list, use_container_width=True, hide_index=True)
    else:
        st.info("No upcoming assignments claimed yet.")
else:
    st.info("No assignments claimed yet. Be the first!")
