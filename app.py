import streamlit as st
import gspread
import json

st.title("Outpeer Leaderboard")

@st.cache_resource
def save_credentials():
    credentials = st.secrets["gcp_service_account"]

    # Save credentials to file
    with open("service_account.json", "w") as f:
        json.dump(credentials, f)

# Save credentials to file
save_credentials()

# Open the Google Sheet
gc = gspread.service_account(filename="service_account.json")
sh = gc.open("Leader Board outpeer.kz courses")

