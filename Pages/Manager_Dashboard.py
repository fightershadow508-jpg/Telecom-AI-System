import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# --- UTILITY FUNCTION (Sentiment Logic copied for display) ---
def analyze_sentiment(text):
    text = str(text).lower()
    negative_words = ['slow', 'not working', 'disconnected', 'high bill', 'overcharged', 'rude', 'unhappy', 'worst', 'bad', 'angry', 'terrible', 'frustrated']
    positive_words = ['solved', 'fixed', 'thank', 'great', 'happy', 'good', 'satisfied', 'resolved']
    
    neg_count = sum(text.count(word) for word in negative_words)
    pos_count = sum(text.count(word) for word in positive_words)
    
    if neg_count > pos_count and neg_count >= 1:
        return 'Negative'
    elif pos_count > neg_count and pos_count >= 1:
        return 'Positive'
    else:
        return 'Neutral'

# --- SECURITY CHECK: Restrict Access (MUST BE AT THE VERY TOP) ---
if 'logged_in' not in st.session_state or st.session_state.logged_in == False:
    st.set_page_config(page_title="Access Denied", layout="wide") 
    st.title("🔒 Access Denied: Login Required")
    st.warning("⚠️ Please log in to access this secure area.")
    
    # --- RESTORED BUTTON ---
    # Show the button to redirect back to the main login page
    if st.button("⬅️ Go to Login/Register Page", type="primary"):
        st.switch_page("streamlit_app.py") 
        
    st.stop() # Stops execution if NOT logged in.

if st.session_state.is_manager == False:
    st.set_page_config(page_title="Access Denied", layout="wide")
    st.title("🚫 Access Denied: Manager Privileges Required")
    st.warning("⚠️ You are logged in as an Agent. Only Manager users can view this dashboard.")
    st.info("Return to the Home page to log in with Manager credentials.")
    st.stop()


# Rest of the code runs ONLY if the user is a Manager
# ----------------------------------------------------

st.set_page_config(page_title="Manager Dashboard - Analytics", layout="wide")

# --- UTILITY: Load & Save Data ---
current_dir = os.path.dirname(__file__)
parent_dir = os.path.join(current_dir, '..')
DATA_PATH = os.path.join(parent_dir, 'processed_data_for_dashboard.csv')

def load_data():
    try:
        df = pd.read_csv(DATA_PATH)
        # Convert date column for time-series analysis
        # Using 'Date' column (dd-mm-yyyy) for parsing to avoid issues
        df['Date_parsed'] = pd.to_datetime(df['Date'], format='%d-%m-%Y', errors='coerce')
        
        # Add Sentiment Column if not exists
        if 'Customer_Sentiment' not in df.columns:
             df['Customer_Sentiment'] = df['Customer_Complaint'].apply(analyze_sentiment)
             
        return df
    except FileNotFoundError:
        st.error("Processed Data file not found. Please ensure you have run the '_train_model.py' script successfully to create it.")
        st.stop()

def save_data(df):
    # Remove temporary columns before saving
    cols_to_drop = ['Date_parsed', 'Customer_Sentiment'] 
    df_to_save = df.drop(columns=[c for c in cols_to_drop if c in df.columns])
    df_to_save.to_csv(DATA_PATH, index=False)

# Load Initial Data
df = load_data()


# --- SIDEBAR (Aesthetic) ---
access_level = 'Manager'
st.sidebar.markdown("### 🧑‍💻 Status Panel")
st.sidebar.markdown(f"**Access Level:** :blue[{access_level}]")
st.sidebar.markdown(f"**Username:** {st.session_state.get('username', 'Manager')}")
st.sidebar.markdown("---") 
st.sidebar.markdown("### 🧭 Main Modules")
st.sidebar.markdown("---")
if st.sidebar.button("🚪 Logout", key="logout_btn_sidebar_md", type="secondary", use_container_width=True):
    st.session_state.logged_in = False
    st.session_state.is_manager = False
    st.switch_page("streamlit_app.py")


# --- UI Setup ---
st.markdown("# 📊 Manager Dashboard: Live Operations Center")
st.markdown(f"**Last Sync:** {datetime.now().strftime('%d-%b-%Y %I:%M %p')}")
st.markdown("---")

# -----------------------------------------------------------
# 1. DAILY LIVE TRACKER (New Feature)
# -----------------------------------------------------------
st.subheader("📅 Today's Live Status")

today_date = pd.to_datetime('today').normalize()
# Filter data for today based on parsed date
if 'Date_parsed' in df.columns:
    df_today = df[df['Date_parsed'] == today_date]
else:
    df_today = df # Fallback

total_today = len(df_today)
solved_today = len(df_today[df_today['Status_Group'] == 'Resolved'])
pending_today = len(df_today[df_today['Status_Group'] == 'Unresolved'])

# Metric Cards Container
with st.container(border=True):
    t_col1, t_col2, t_col3 = st.columns(3)
    t_col1.metric("📢 Complaints Received Today", total_today, delta="Live Count")
    t_col2.metric("✅ Solved Today", solved_today, delta_color="normal")
    t_col3.metric("⏳ Pending Today", pending_today, delta_color="inverse")

st.markdown("---")

# -----------------------------------------------------------
# 2. EXECUTIVE SUMMARY & CHARTS (Overall Performance)
# -----------------------------------------------------------
st.header("📈 Overall Performance Analytics")

# --- KPIs ---
total_complaints = len(df)
resolved_count = len(df[df['Status_Group'] == 'Resolved'])
unresolved_count = len(df[df['Status_Group'] == 'Unresolved'])
resolution_rate = (resolved_count / total_complaints) * 100 if total_complaints > 0 else 0

with st.container(border=True):
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    col1.metric("Total Complaints Tracked", total_complaints)
    col2.metric("Resolved Cases", resolved_count)
    col3.metric("Pending/Escalated", unresolved_count, delta_color="inverse")
    col4.metric("Resolution Rate", f"{resolution_rate:.1f}%")

st.markdown("---")

# --- Deep Dive Analytics Charts ---
st.header("Deep Dive Analytics")

# Row 1: Resolution Status & Complaint Categories
chart_col1, chart_col2 = st.columns([1, 1])

# Graph 1: Resolution Status Distribution (Donut Chart)
status_fig = px.pie(df, names='Status_Group', title='Complaint Resolution Status', hole=0.5,
                    color_discrete_map={'Resolved':'#2ECC71', 'Unresolved':'#E74C3C'}, 
                    template="plotly_dark") 

# Graph 2: Top Complaint Types (Bar Chart)
type_counts = df['Complaint_Type'].value_counts().reset_index()
type_counts.columns = ['Complaint Type', 'Count']
type_fig = px.bar(type_counts, x='Complaint Type', y='Count', 
                  title='Distribution of Complaint Categories', 
                  color='Count', color_continuous_scale=px.colors.sequential.Plasma,
                  template="plotly_dark")

with chart_col1:
    st.plotly_chart(status_fig, use_container_width=True)

with chart_col2:
    st.plotly_chart(type_fig, use_container_width=True)

# Row 2: Geo & Time Series
geo_col, time_col = st.columns(2)

with geo_col:
    state_counts = df['State'].value_counts().reset_index()
    state_counts.columns = ['State', 'Total Complaints']
    state_fig = px.bar(state_counts.nlargest(10, 'Total Complaints'), x='State', y='Total Complaints',
                       title='Top 10 States by Complaint Volume',
                       color='Total Complaints', color_continuous_scale=px.colors.sequential.Teal,
                       template="plotly_dark")
    st.plotly_chart(state_fig, use_container_width=True)

with time_col:
    # Ensure Date_month_year is datetime for sorting
    df['Date_month_year_dt'] = pd.to_datetime(df['Date_month_year'], format='%d-%b-%y', errors='coerce')
    time_counts = df.set_index('Date_month_year_dt').resample('M').size().reset_index(name='Count')
    time_fig = px.line(time_counts, x='Date_month_year_dt', y='Count', 
                       title='Monthly Trend of Total Complaints',
                       markers=True,
                       template="plotly_dark")
    st.plotly_chart(time_fig, use_container_width=True)

st.markdown("---") 

# -----------------------------------------------------------
# 3. INTERACTIVE COMPLAINT MANAGEMENT (Data Editor)
# -----------------------------------------------------------
st.header("📝 Complaint Management Desk")
st.info("Filter, Review, and Resolve complaints directly here. Changes are saved to the database.")

# Filter Options
filter_status = st.radio("Filter View:", ["All", "Unresolved Only", "Resolved Only"], horizontal=True)

# Filtering Logic
if filter_status == "Unresolved Only":
    filtered_df = df[df['Status_Group'] == 'Unresolved']
elif filter_status == "Resolved Only":
    filtered_df = df[df['Status_Group'] == 'Resolved']
else:
    filtered_df = df

# Columns to show in editor
# Adding 'Customer_Sentiment' so manager can see mood
edit_cols = ['Ticket_#', 'Date', 'Customer_Complaint', 'Customer_Sentiment', 'Complaint_Type', 'Status_Group']

# DATA EDITOR WIDGET
edited_df = st.data_editor(
    filtered_df[edit_cols].sort_values(by='Date', ascending=False), # Show latest first (approx)
    column_config={
        "Ticket_#": st.column_config.TextColumn("Ticket ID", disabled=True),
        "Date": st.column_config.TextColumn("Date", disabled=True),
        "Customer_Complaint": st.column_config.TextColumn("Complaint Details", width="large", disabled=True),
        "Customer_Sentiment": st.column_config.TextColumn("Mood", width="small", disabled=True),
        "Complaint_Type": st.column_config.TextColumn("Category", disabled=True),
        "Status_Group": st.column_config.SelectboxColumn(
            "Resolution Status",
            options=["Resolved", "Unresolved"],
            required=True,
            help="Double-click to change status."
        )
    },
    hide_index=True,
    num_rows="fixed",
    use_container_width=True,
    key="complaint_editor"
)

# SAVE BUTTON
if st.button("💾 Save Status Updates", type="primary"):
    try:
        # 1. Create a map of Ticket ID to NEW Status from the edited table
        status_map = dict(zip(edited_df['Ticket_#'].astype(str), edited_df['Status_Group']))
        
        # 2. Update the ORIGINAL dataframe using this map
        df['Ticket_#'] = df['Ticket_#'].astype(str)
        df['Status_Group'] = df['Ticket_#'].map(status_map).fillna(df['Status_Group'])
        
        # 3. Update the detailed 'Status' column too for consistency
        df.loc[df['Status_Group'] == 'Resolved', 'Status'] = 'Solved'
        df.loc[df['Status_Group'] == 'Unresolved', 'Status'] = 'Open'
        
        # 4. Save back to CSV
        save_data(df)
        
        st.success("✅ Database Updated Successfully! Dashboard will refresh.")
        st.rerun()
        
    except Exception as e:
        st.error(f"Error saving data: {e}")

st.caption("Instructions: Double click on 'Resolution Status' cell to change it from Unresolved to Resolved.")