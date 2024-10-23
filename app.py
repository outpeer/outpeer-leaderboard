import streamlit as st
import json
import os
from streamlit_gsheets import GSheetsConnection
st.title("Outpeer Leaderboard")

st.title("Read Google Sheet as DataFrame")

conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(worksheet="LeaderBoard DS TO24")

st.dataframe(df)