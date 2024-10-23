import streamlit as st
from google.oauth2 import service_account
import gspread

st.title("Outpeer Leaderboard")

@st.cache_resource
def save_credentials():
    # Create credentials object
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"]
    )

    # Save credentials to file
    with open("service_account.json", "w") as f:
        f.write(credentials.to_json())

# Save credentials to file
save_credentials()

# Open the Google Sheet
gc = gspread.service_account(filename="service_account.json")
sh = gc.open("Leader Board outpeer.kz courses")

