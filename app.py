import streamlit as st
import json
import os
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
st.title("Outpeer Leaderboard")

@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)

@st.cache_data
def pull_leaderboard_data(fetching_date: str):
    print(f"Fetching leaderboard data for {fetching_date}")
    conn = get_connection()
    leaderboard_ds = conn.read(worksheet="LeaderBoard DS TO24")
    leaderboard_da = conn.read(worksheet="LeaderBoard DA TO24")
    leaderboard_pe = conn.read(worksheet="LeaderBoard PE TO24")
    leaderboard_ai = conn.read(worksheet="LeaderBoard AI TO24")
    return {
        "DS": leaderboard_ds,
        "DA": leaderboard_da,
        "PE": leaderboard_pe,
        "AI": leaderboard_ai,
    }

@st.cache_data
def pull_homework_data(fetching_date: str):
    print(f"Fetching homework data for {fetching_date}")
    conn = get_connection()
    homework_ds = conn.read(worksheet="HW DS TO24")
    homework_da = conn.read(worksheet="HW DA TO24")
    homework_pe = conn.read(worksheet="HW PE TO24")
    homework_ai = conn.read(worksheet="HW AI TO24")
    return {
        "DS": homework_ds,
        "DA": homework_da,
        "PE": homework_pe,
        "AI": homework_ai,
    }

@st.cache_data
def pull_attendance_data(fetching_date: str):
    print(f"Fetching attendance data for {fetching_date}")
    conn = get_connection()
    attendance_ds = conn.read(worksheet="Attendance DS TO24")
    attendance_da = conn.read(worksheet="Attendance DA TO24")
    attendance_pe = conn.read(worksheet="Attendance PE TO24")
    attendance_ai = conn.read(worksheet="Attendance AI TO24")
    return {
        "DS": attendance_ds,
        "DA": attendance_da,
        "PE": attendance_pe,
        "AI": attendance_ai,
    }

map_course_to_label = {
    "DS": "Data Science",
    "DA": "Data Analytics",
    "PE": "Python Engineering",
    "AI": "AI Engineering",
}

course = st.selectbox(
    "Курс на котором Вы обучаетесь", 
    ["DS", "DA", "PE", "AI"],
    format_func=lambda x: map_course_to_label[x]
)

student_id = st.text_input("Введите Ваш ИИН")

fetching_date = datetime.now().strftime("%Y-%m-%d")
leaderboard_data = pull_leaderboard_data(fetching_date)
homework_data = pull_homework_data(fetching_date)
attendance_data = pull_attendance_data(fetching_date)

if course:
    leaderboard_df = leaderboard_data[course]
    st.write(leaderboard_df)

if student_id and course:
    leaderboard_df = leaderboard_data[course][leaderboard_data[course]["ИИН"] == student_id]
    homework_df = homework_data[course][homework_data[course]["ИИН"] == student_id]
    attendance_df = attendance_data[course][attendance_data[course]["ИИН"] == student_id]

    st.dataframe(leaderboard_df)
    st.dataframe(homework_df)
    st.dataframe(attendance_df)
