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
    
    attendance_ds = conn.read(worksheet="Attendance DS TO24", dtype=dtype_spec)
    attendance_da = conn.read(worksheet="Attendance DA TO24", dtype=dtype_spec)
    attendance_pe = conn.read(worksheet="Attendance PE TO24", dtype=dtype_spec)
    attendance_ai = conn.read(worksheet="Attendance AI TO24", dtype=dtype_spec)

    return {
        "DS": attendance_ds,
        "DA": attendance_da,
        "PE": attendance_pe,
        "AI": attendance_ai,
    }

def get_rating_chart(min_score, max_score, student_score, student_rank, total_participants):
    leader_text = 'Лидер #1'
    student_rating_text = f'Ваш рейтинг #{int(student_rank)}'
    last_place_text = f'Последнее место #{total_participants}'
    chart_data = pd.DataFrame({
        'Category': [leader_text, student_rating_text, last_place_text],
        'Score': [max_score, student_score, min_score],
    })
    
    # Sort the data by score in descending order
    chart_data = chart_data.sort_values('Score', ascending=True)

    # Create the horizontal bar chart
    fig = px.bar(chart_data, y='Category', x='Score', orientation='h',
                 title='Ваше место в рейтинге',
                 labels={'Score': 'Балл', 'Category': ''},
                 color='Category',
                 color_discrete_map={leader_text: 'lightgrey', student_rating_text: 'red', last_place_text: 'lightgrey'},
                 height=300)

    # Customize the layout
    fig.update_layout(
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=20),
        yaxis=dict(autorange="reversed")  # This ensures the order is preserved
    )

    return fig

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

st.write("---")

fetching_date = datetime.now().strftime("%Y-%m-%d")
leaderboard_data = pull_leaderboard_data(fetching_date)
homework_data = pull_homework_data(fetching_date)
attendance_data = pull_attendance_data(fetching_date)

if student_id and course:
    leaderboard_df = leaderboard_data[course]
    student_leaderboard_df = leaderboard_df[leaderboard_df["ИИН"] == student_id]

    if student_leaderboard_df.empty:
        st.error("Вас нет в лидерборде. Пожалуйста, проверьте правильность ввода ИИН или курса.")
        st.stop()

    name_russian = student_leaderboard_df["ФИО"].values[0]
    name_english = student_leaderboard_df["ФИО на латинице"].values[0]

    if name_english != "":
        st.subheader(f"{name_russian} ({name_english}). ")
    else:
        st.subheader(f"{name_russian}. ")
    
    st.write("---")
    max_leaderboard_score = leaderboard_df["Total score"].max()
    min_leaderboard_score = leaderboard_df["Total score"].min()
    student_leaderboard_score = student_leaderboard_df["Total score"].values[0]
    student_leaderboard_rank = student_leaderboard_df["Рейтинг"].values[0]
    rating_chart = get_rating_chart(
        min_leaderboard_score, 
        max_leaderboard_score, 
        student_leaderboard_score, 
        student_leaderboard_rank, 
        len(leaderboard_df)
    )
    st.plotly_chart(rating_chart)

    st.write("---")
    homework_df = homework_data[course]
    hw_columns = [col for col in homework_df.columns if col.startswith("HW")]
    # drop columns that have all null values (no homework submitted)
    relevant_homework_df = homework_df[hw_columns].dropna(axis=1, how="all")
    count_homeworks = len(relevant_homework_df.columns)
    hw_avg_score_class = (relevant_homework_df.sum(axis=1) / count_homeworks).mean()
    hw_avg_scores = relevant_homework_df.mean(axis=0).values
    hw_avg_scores = [
        hw_avg_score for hw_avg_score in hw_avg_scores
    ] + [None] * (len(hw_columns) - len(hw_avg_scores))

    student_homework_df = homework_df[homework_df["ИИН"] == student_id]
    hw_labels = [str(col[2:]) for col in hw_columns]
    hw_scores = student_homework_df[hw_columns].iloc[0].values
    hw_avg_score = sum([score for score in hw_scores if not pd.isna(score)]) / count_homeworks
    hw_student_data = pd.DataFrame({
        "labels": hw_labels,
        "scores": hw_scores,
        "type": ["Ваш балл"] * len(hw_labels),
    })
    hw_class_data = pd.DataFrame({
        "labels": hw_labels,
        "scores": hw_avg_scores,
        "type": ["Класс"] * len(hw_labels),
    })
    hw_data = pd.concat([hw_class_data, hw_student_data])
    hw_chart = px.bar(
        hw_data,
        x="labels", 
        y="scores",
        color="type",
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

    st.write("---")
    attendance_df = attendance_data[course]
    col_dates_start_index = attendance_df.columns.get_loc("Week 1")
    student_attendance_df = attendance_df[attendance_df["ИИН"] == student_id]
    lesson_dates = attendance_df.iloc[0][col_dates_start_index:]
    lesson_dates = lesson_dates[lesson_dates.notna()]
    lesson_dates = lesson_dates.tolist()
    lesson_dates = [datetime.strptime(date, "%d.%m.%y") for date in lesson_dates]
    total_lessons = len(lesson_dates)
    attendance_scores = student_attendance_df.iloc[0][col_dates_start_index:total_lessons+col_dates_start_index+1]
    attendance_scores = attendance_scores.tolist()
    attendance_data = list(zip(lesson_dates, attendance_scores))
    attendance_data = pd.DataFrame({
        "dates": [date for date, _ in attendance_data],
        "scores": [score for _, score in attendance_data],
    })
    attendance_avg_score = sum([score for score in attendance_data["scores"] if not pd.isna(score)]) / len(attendance_data)

    attendance_chart = px.bar(
        attendance_data,
        x="dates",
        y="scores",
        labels={"dates": "Дата уроков", "scores": ""},
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
