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
    chart_data = pd.DataFrame({
        'Category': ['Your Score'],
        'Min': [min_score],
        'Score': [student_score],
        'Max': [max_score]
    })

    # Create the horizontal bar chart
    fig = px.bar(chart_data, y='Category', x=['Min', 'Score', 'Max'], orientation='h',
                 title='Your Score Compared to Min and Max',
                 labels={'value': 'Score', 'variable': 'Type'},
                 color_discrete_map={'Min': 'lightgrey', 'Score': 'green', 'Max': 'lightgrey'},
                 height=200)

    # Add ranking labels
    fig.add_annotation(
        x=min_score, 
        y=0, 
        text=f"Rank: {total_participants}", 
        showarrow=False, 
        yshift=-20
    )
    fig.add_annotation(
        x=student_score, 
        y=0, 
        text=f"Your Rank: {int(student_rank)}", 
        showarrow=False, 
        yshift=20, 
        font=dict(color="green")
    )
    fig.add_annotation(
        x=max_score, 
        y=0, 
        text="Rank: 1", 
        showarrow=False, 
        yshift=-20
    )

    # Customize the layout
    fig.update_layout(
        showlegend=False,
        xaxis_title="Score",
        yaxis_title="",
        yaxis_showticklabels=False,
        margin=dict(l=0, r=0, t=40, b=0)
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

fetching_date = datetime.now().strftime("%Y-%m-%d")
leaderboard_data = pull_leaderboard_data(fetching_date)
homework_data = pull_homework_data(fetching_date)
attendance_data = pull_attendance_data(fetching_date)

if course:
    leaderboard_df = leaderboard_data[course]
    attendance_df = attendance_data[course]
    homework_df = homework_data[course]
    st.write(leaderboard_df)
    st.write(attendance_df)
    st.write(homework_df)

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

    name_russian = student_leaderboard_df["ФИО"].values[0]
    name_english = student_leaderboard_df["ФИО на латинице"].values[0]

    if name_english != "":
        st.title(f"Результаты Вашего прогресса, {name_russian} ({name_english}). ")
    else:
        st.title(f"Результаты Вашего прогресса, {name_russian}. ")

    student_leaderboard_score = student_leaderboard_df["Total score"].values[0]
    student_leaderboard_rank = student_leaderboard_df["Рейтинг"].values[0]

    st.write("---")
    st.write("**Ваш текущий рейтинг:**")    
    st.write(f"{int(student_leaderboard_rank)}")
    st.write(f"Общее количество участников: {len(leaderboard_df)}")

    st.write("---")

    st.write("**Ваш текущий балл:**")
    st.write(f"{student_leaderboard_score}")
    st.write("**Максимальный балл:**")
    st.write(f"{max_leaderboard_score}")
    st.write("**Минимальный балл:**")
    st.write(f"{min_leaderboard_score}")

    st.write("---")

    fig = get_rating_chart(
        min_leaderboard_score, 
        max_leaderboard_score, 
        student_leaderboard_score, 
        student_leaderboard_rank, 
        len(leaderboard_df)
    )
    st.plotly_chart(fig)

    st.write("---")
    hw_columns = [col[3:] for col in student_homework_df.columns if col.startswith("HW")]
    hw_scores = student_homework_df[hw_columns].iloc[0]

    fig = px.bar(
        x=hw_columns, 
        y=hw_scores, 
        labels={"x": "Домашние задания", "y": "Баллы"}, 
        title="Ваши домашние задания",
    )
    fig.update_layout(yaxis_range=[0, 100])
    st.plotly_chart(fig)

    st.write("---")


    st.dataframe(leaderboard_df)
    st.dataframe(homework_df)
    st.dataframe(attendance_df)
