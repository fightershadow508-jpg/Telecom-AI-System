import streamlit as st
import pandas as pd
import os
import subprocess # <-- Nayi library shamil ki

# --- RUN TRAINING SCRIPT FIRST (Self-healing fix) ---
# Check karte hain ke kya model file available hai. Agar nahi hai (deployment par), 
# toh _train_model.py ko run karo taake woh zaroori .pkl aur .csv files bana de.
if not os.path.exists('type_classifier_model.pkl'):
    try:
        # _train_model.py ko chalao
        subprocess.run(["python", "_train_model.py"], check=True)
        print("INFO: _train_model.py executed successfully to create missing files.")
    except subprocess.CalledProcessError as e:
        st.error(f"FATAL ERROR: Model training script failed to run. Error: {e}")
        st.stop()
    except FileNotFoundError:
        st.error("FATAL ERROR: _train_model.py not found in the root directory.")
        st.stop()
# ---------------------------------------------------

# --- Configuration & File Path ---
MANAGER_USERNAME = "manager"
MANAGER_PASSWORD = "data_master"
USER_FILE = "registered_users.csv"

# --- Setup Page Config ---
st.set_page_config(
    page_title="Telecom Complaint Resolution System",
    page_icon="🤖",
    layout="wide"
)

# --- Utility Functions ---
def load_users():
    if os.path.exists(USER_FILE):
        return pd.read_csv(USER_FILE)
    else:
        # Create a blank DataFrame if file does not exist
        df = pd.DataFrame(columns=['Username', 'Password'])
        df.to_csv(USER_FILE, index=False)
        return df

def register_user(username, password):
    df = load_users()
    if username in df['Username'].values:
        return False 
    
    new_user = pd.DataFrame({'Username': [username], 'Password': [password]})
    df = pd.concat([df, new_user], ignore_index=True)
    df.to_csv(USER_FILE, index=False)
    return True

def verify_user(username, password):
    df = load_users()
    # Check Manager access first
    if username == MANAGER_USERNAME and password == MANAGER_PASSWORD:
        return "Manager"
    
    # Check Registered User access
    user_match = df[(df['Username'] == username) & (df['Password'] == password)]
    if not user_match.empty:
        return "Agent"
    
    return None

# Function to set session state after successful login
def set_page_access(is_manager):
    st.session_state.is_manager = is_manager
    st.session_state.logged_in = True

# Function to display the Home/Login screen
def show_login_page():
    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.is_manager = False
        st.session_state.username = None # Initialize username
        
    st.title(":robot: AI-Powered Telecom Complaint Management")
    st.markdown("### Intelligent Resolution & Data Analytics Platform")
    st.markdown("---")
    
    # ----------------- LOGIN / LOGOUT SECTION -----------------
    if st.session_state.logged_in:
        
        # --- SIDEBAR CONTENT (ATTRACTIVE FIX) ---
        access_level = 'Manager' if st.session_state.is_manager else 'Agent'
        
        # 1. SIDEBAR STATUS CARD (Aesthetic)
        st.sidebar.markdown("### 🧑‍💻 Status Panel")
        st.sidebar.markdown(f"**Access Level:** :blue[{access_level}]")
        st.sidebar.markdown(f"**Username:** {st.session_state.username}")
        st.sidebar.markdown("---") 
        
        st.sidebar.markdown("### 🧭 Main Modules")
        
        # 2. LOGOUT BUTTON
        st.sidebar.markdown("---")
        if st.sidebar.button("🚪 Logout", key="logout_btn_sidebar", type="secondary", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.is_manager = False
            st.session_state.username = None
            st.rerun()
        
        # Display Welcome Message (on the main page)
        st.success(f"Welcome, {access_level}! You are successfully logged in. Use the sidebar for navigation.")
        st.markdown("---")
        
    else:
        # --- Login & Registration Form (Side-by-Side) ---
        login_col, register_col = st.columns([1, 1])
        
        with login_col:
            st.subheader("1. Agent/Manager Login")
            with st.form("login_form", border=True):
                login_username = st.text_input("Username", key="l_user")
                login_password = st.text_input("Password", type="password", key="l_pass")
                login_submitted = st.form_submit_button("🔑 Login", type="primary")

                if login_submitted:
                    user_role = verify_user(login_username, login_password)
                    if user_role == "Manager":
                        set_page_access(True)
                        st.session_state.username = login_username # FINAL FIX: Save username
                        st.success("Manager Login Successful! Full Access Granted.")
                        st.rerun()
                    elif user_role == "Agent":
                        set_page_access(False) # Is Agent
                        st.session_state.username = login_username # FINAL FIX: Save username
                        st.success("Agent Login Successful! User Mode Access Granted.")
                        st.rerun()
                    else:
                        st.error("Invalid Username or Password. Please Register first or check credentials.")

        with register_col:
            st.subheader("2. New Agent Registration")
            with st.form("register_form", border=True):
                reg_username = st.text_input("New Username", placeholder="Enter unique username", key="r_user")
                reg_password = st.text_input("New Password", type="password", key="r_pass")
                reg_submitted = st.form_submit_button("✍️ Register New Agent", type="secondary")
                
                if reg_submitted:
                    if not reg_username or not reg_password:
                        st.warning("Please fill in both Username and Password.")
                    elif register_user(reg_username, reg_password):
                        st.success(f"Registration Successful for **{reg_username}**! Now please use the **Login form**.")
                    else:
                        st.error("Username already taken. Please choose another one.")
                        
        st.markdown("---")
        st.info("💡 **Agent Access:** Please Register first, then Login. **Manager Access:** Use specific credentials.")


    # ----------------- NAVIGATION GUIDE (Aesthetic Cards) -----------------
    if st.session_state.logged_in:
        st.header("📋 Application Overview")
        st.markdown("Please use the sidebar to access the following application modes:")

        # Custom CSS for aesthetic cards
        st.markdown("""
        <style>
            .big-font {
                font-size: 18px !important;
                font-weight: bold;
                color: #2E86C1; /* Soft Blue */
            }
        </style>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.image("https://img.icons8.com/color/96/artificial-intelligence.png", width=50)
            st.markdown("### Core AI Model")
            st.markdown('<p class="big-font">Predicts Complaint Type & Customer Mood.</p>', unsafe_allow_html=True)

        with col2:
            st.image("https://img.icons8.com/color/96/dashboard.png", width=50)
            st.markdown("### Data Visualization")
            st.markdown('<p class="big-font">Interactive geographical & time-series analysis.</p>', unsafe_allow_html=True)

        with col3:
            st.image("https://img.icons8.com/color/96/customer-service.png", width=50)
            st.markdown("### Resolution Flow")
            st.markdown('<p class="big-font">Guides agents with Tier 1/Tier 2 action plans.</p>', unsafe_allow_html=True)

        st.markdown("---")
        st.info("Your project combines cutting-edge AI with actionable business intelligence.")

# Run the final login page
show_login_page()