import streamlit as st
import pandas as pd
import plotly.express as px
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
    dtype_spec = {"ИИН": str}
    leaderboard_ds = conn.read(worksheet="LeaderBoard DS TO24", dtype=dtype_spec)
    leaderboard_da = conn.read(worksheet="LeaderBoard DA TO24", dtype=dtype_spec)
    leaderboard_pe = conn.read(worksheet="LeaderBoard PE TO24", dtype=dtype_spec)
    leaderboard_ai = conn.read(worksheet="LeaderBoard AI TO24", dtype=dtype_spec)

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
    dtype_spec = {"ИИН": str}
    homework_ds = conn.read(worksheet="HW DS TO24", dtype=dtype_spec)
    homework_da = conn.read(worksheet="HW DA TO24", dtype=dtype_spec)
    homework_pe = conn.read(worksheet="HW PE TO24", dtype=dtype_spec)
    homework_ai = conn.read(worksheet="HW AI TO24", dtype=dtype_spec)

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
    
    # Specify dtype for the "ИИН" column
    dtype_spec = {"ИИН": str}

    def read_attendance_sheet(worksheet):
        df = conn.read(worksheet=worksheet, dtype=dtype_spec)
        # Combine multi-level columns
        df.columns = [f"{col[0]}_{col[1]}" if isinstance(col, tuple) else col for col in df.columns]
        return df
    
    attendance_ds = read_attendance_sheet("Attendance DS TO24")
    attendance_da = read_attendance_sheet("Attendance DA TO24")
    attendance_pe = read_attendance_sheet("Attendance PE TO24")
    attendance_ai = read_attendance_sheet("Attendance AI TO24")

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
    "Курс, на котором Вы обучаетесь", 
    [None, "DS", "DA", "PE", "AI"],
    index=0,
    format_func=lambda x: map_course_to_label[x] if x else ""
)

student_id = st.text_input("Ваш ИИН")

fetching_date = datetime.now().strftime("%Y-%m-%d")
leaderboard_data = pull_leaderboard_data(fetching_date)
homework_data = pull_homework_data(fetching_date)
attendance_data = pull_attendance_data(fetching_date)

if course:
    leaderboard_df = leaderboard_data[course]
    attendance_df = attendance_data[course]
    st.write(leaderboard_df)
    st.write(attendance_df)

if student_id and course:
    leaderboard_df = leaderboard_data[course]
    homework_df = homework_data[course]
    attendance_df = attendance_data[course]

    max_leaderboard_score = leaderboard_df["Total score"].max()
    min_leaderboard_score = leaderboard_df["Total score"].min()

    student_leaderboard_df = leaderboard_df[leaderboard_df["ИИН"] == student_id]
    student_homework_df = homework_df[homework_df["ИИН"] == student_id]
    student_attendance_df = attendance_df[attendance_df["ИИН"] == student_id]

    if student_leaderboard_df.empty:
        st.error("Вас нет в лидерборде. Пожалуйста, проверьте правильность ввода ИИН или курса.")
        st.stop()

    name_russian = leaderboard_df["ФИО"].values[0]
    name_english = leaderboard_df["ФИО на латинице"].values[0]

    if name_english != "":
        st.title(f"Результаты Вашего прогресса, {name_russian} ({name_english}). ")
    else:
        st.title(f"Результаты Вашего прогресса, {name_russian}. ")

    student_leaderboard_score = student_leaderboard_df["Total score"].values[0]
    student_leaderboard_rank = student_leaderboard_df["Рейтинг"].values[0]

    st.write("---")
    st.write("**Ваш текущий рейтинг:**")    
    st.write(f"{student_leaderboard_rank} / общее количество участников: {len(leaderboard_df)}")

    st.write("---")

    st.write("**Ваш текущий балл:**")
    st.write(f"{student_leaderboard_score}")
    st.write("**Максимальный балл:**")
    st.write(f"{max_leaderboard_score}")
    st.write("**Минимальный балл:**")
    st.write(f"{min_leaderboard_score}")

    st.write("---")

    st.write("**Ваши домашние задания:**")
    hw_columns = [col for col in student_homework_df.columns if col.startswith("HW")]
    hw_scores = student_attendance_df[hw_columns].iloc[0]

    fig = px.bar(x=hw_columns, y=hw_scores, labels={"x": "Домашние задания", "y": "Баллы"}, title="Ваши домашние задания")
    st.plotly_chart(fig)

    st.write("---")


    st.dataframe(leaderboard_df)
    st.dataframe(homework_df)
    st.dataframe(attendance_df)
