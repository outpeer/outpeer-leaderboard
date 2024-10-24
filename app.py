import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# Constants
COURSES = ["DS", "DA", "PE", "AI"]
COURSE_LABELS = {
    "DS": "Data Science",
    "DA": "Data Analytics",
    "PE": "Python Engineering",
    "AI": "AI Engineering",
}

# Setup
st.title("Outpeer Leaderboard")

@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)

@st.cache_data
def pull_data(data_type: str, fetching_date: str):
    print(f"Fetching {data_type} data for {fetching_date}")
    conn = get_connection()
    dtype_spec = {"ИИН": str}
    return {
        course: conn.read(worksheet=f"{data_type} {course} TO24", dtype=dtype_spec)
        for course in COURSES
    }

def get_rating_chart(min_score, max_score, student_score, student_rank, total_participants):
    chart_data = pd.DataFrame({
        'Category': ['Лидер #1', f'Ваш рейтинг #{int(student_rank)}', f'Последнее место #{total_participants}'],
        'Score': [max_score, student_score, min_score],
    })
    
    fig = px.bar(chart_data.sort_values('Score', ascending=True), 
                 y='Category', x='Score', orientation='h',
                 title='Ваше место в рейтинге',
                 labels={'Score': 'Балл', 'Category': ''},
                 color='Category',
                 color_discrete_map={'Лидер #1': 'lightgrey', f'Ваш рейтинг #{int(student_rank)}': 'red', f'Последнее место #{total_participants}': 'lightgrey'},
                 height=300)

    fig.update_layout(
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=20),
        yaxis=dict(autorange="reversed")
    )

    return fig

def display_student_info(student_leaderboard_df):
    name_russian = student_leaderboard_df["ФИО"].values[0]
    name_english = student_leaderboard_df["ФИО на латинице"].values[0]
    st.subheader(f"{name_russian} ({name_english})" if name_english else f"{name_russian}")

def display_rating_chart(leaderboard_df, student_leaderboard_df):
    max_score = leaderboard_df["Total score"].max()
    min_score = leaderboard_df["Total score"].min()
    student_score = student_leaderboard_df["Total score"].values[0]
    student_rank = student_leaderboard_df["Рейтинг"].values[0]
    rating_chart = get_rating_chart(min_score, max_score, student_score, student_rank, len(leaderboard_df))
    st.plotly_chart(rating_chart)

def display_homework_chart(homework_df, student_id):
    hw_columns = [col for col in homework_df.columns if col.startswith("HW")]
    relevant_homework_df = homework_df[hw_columns].dropna(axis=1, how="all")
    count_homeworks = len(relevant_homework_df.columns)
    
    hw_avg_score_class = (relevant_homework_df.sum(axis=1) / count_homeworks).mean()
    hw_avg_scores = relevant_homework_df.mean(axis=0).values
    hw_avg_scores = [*hw_avg_scores, *[None] * (len(hw_columns) - len(hw_avg_scores))]

    student_homework_df = homework_df[homework_df["ИИН"] == student_id]
    hw_labels = [str(col[2:]) for col in hw_columns]
    hw_scores = student_homework_df[hw_columns].iloc[0].values
    hw_avg_score = sum([score for score in hw_scores if not pd.isna(score)]) / count_homeworks

    hw_data = pd.concat([
        pd.DataFrame({"labels": hw_labels, "scores": hw_avg_scores, "type": ["Класс"] * len(hw_labels)}),
        pd.DataFrame({"labels": hw_labels, "scores": hw_scores, "type": ["Ваш балл"] * len(hw_labels)})
    ])

    hw_chart = px.bar(
        hw_data,
        x="labels", y="scores", color="type",
        color_discrete_map={"Ваш балл": "blue", "Класс": "lightgrey"},
        category_orders={"type": ["Класс", "Ваш балл"]},
        labels={"labels": "Домашние задания", "scores": "", "type": "Класс/Ваш балл"}, 
        title="Ваши домашние задания",
        barmode="group",
    )
    hw_chart.update_layout(yaxis_range=[0, 100])
    hw_chart.add_hline(
        y=hw_avg_score,
        line_dash="dash",
        line_color="red" if hw_avg_score < hw_avg_score_class else "green",
        annotation_text=f"Ваш средний балл: {hw_avg_score:.2f}",
        annotation_position="top right",
    )
    hw_chart.add_hline(
        y=hw_avg_score_class,
        line_dash="dash",
        line_color="black",
        annotation_text=f"Средний балл класса: {hw_avg_score_class:.2f}",
        annotation_position="top right",
    )
    st.plotly_chart(hw_chart)

def display_attendance_chart(attendance_df, student_id):
    col_dates_start_index = attendance_df.columns.get_loc("Week 1")
    student_attendance_df = attendance_df[attendance_df["ИИН"] == student_id]
    lesson_dates = attendance_df.iloc[0][col_dates_start_index:]
    lesson_dates = [datetime.strptime(date, "%d.%m.%y") for date in lesson_dates[lesson_dates.notna()].tolist()]
    total_lessons = len(lesson_dates)
    attendance_scores = student_attendance_df.iloc[0][col_dates_start_index:total_lessons+col_dates_start_index+1].tolist()

    attendance_data = pd.DataFrame({
        "dates": lesson_dates,
        "scores": attendance_scores,
    })
    attendance_avg_score = sum([score for score in attendance_data["scores"] if not pd.isna(score)]) / len(attendance_data)

    attendance_chart = px.bar(
        attendance_data,
        x="dates", y="scores",
        labels={"dates": "Даты уроков", "scores": ""},
        title="Ваша посещаемость",
    )
    attendance_chart.update_layout(yaxis_range=[0, 1.1])
    attendance_chart.add_hline(
        y=attendance_avg_score,
        line_dash="solid",
        line_color="red",
        annotation_text=f"Средняя посещаемость: {100 * attendance_avg_score:.0f}%",
        annotation_position="top right",
    )
    st.plotly_chart(attendance_chart)

# Main
course = st.selectbox(
    "Курс, на котором Вы обучаетесь", 
    [None, *COURSES],
    index=0,
    format_func=lambda x: COURSE_LABELS.get(x, "")
)

student_id = st.text_input("Ваш ИИН")

if student_id and course:
    fetching_date = datetime.now().strftime("%Y-%m-%d")
    leaderboard_data = pull_data("LeaderBoard", fetching_date)
    homework_data = pull_data("HW", fetching_date)
    attendance_data = pull_data("Attendance", fetching_date)

    leaderboard_df = leaderboard_data[course]
    student_leaderboard_df = leaderboard_df[leaderboard_df["ИИН"] == student_id]

    if student_leaderboard_df.empty:
        st.error("Вас нет в лидерборде. Пожалуйста, проверьте правильность ввода ИИН или курса.")
        st.stop()

    display_student_info(student_leaderboard_df)
    st.write("---")
    display_rating_chart(leaderboard_df, student_leaderboard_df)
    st.write("---")
    display_homework_chart(homework_data[course], student_id)
    st.write("---")
    display_attendance_chart(attendance_data[course], student_id)
