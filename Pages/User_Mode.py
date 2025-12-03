import streamlit as st
import joblib
import re
import pandas as pd
import os

# --- SECURITY CHECK: Restrict Access (MUST BE AT THE VERY TOP) ---
if 'logged_in' not in st.session_state or st.session_state.logged_in == False:
    st.set_page_config(page_title="Access Denied", layout="wide") 
    st.title("🔒 Access Denied")
    st.warning("⚠️ Access Denied: Please log in to view this Agent Dashboard.")
    st.info("Return to the Home page to log in or register a new account.")
    
    # --- FINAL FIX: ADD BUTTON FOR REDIRECT ---
    if st.button("⬅️ Go to Login/Register Page", type="primary"):
        st.switch_page("streamlit_app.py") # Redirects to the main login/register page
        
    st.stop() # Stops execution if access is not granted

# ---------------------------------------------------------------------------------------
# CODE FLOW START (ONLY IF LOGGED IN)

st.set_page_config(page_title="Agent Mode - Smart Resolution", layout="wide") # Actual page config runs only if secured

# --- Utility Functions (Same) ---
def analyze_sentiment(text):
    text = text.lower()
    negative_words = ['slow', 'not working', 'disconnected', 'high bill', 'overcharged', 'rude', 'unhappy', 'worst', 'bad', 'angry', 'terrible', 'frustrated']
    positive_words = ['solved', 'fixed', 'thank', 'great', 'happy', 'good', 'satisfied', 'resolved']
    
    neg_count = sum(text.count(word) for word in negative_words)
    pos_count = sum(text.count(word) for word in positive_words)
    
    if neg_count > pos_count and neg_count >= 1:
        return 'Negative', '😡'
    elif pos_count > neg_count and pos_count >= 1:
        return 'Positive', '😊'
    else:
        return 'Neutral', '😐'

def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text) 
    return text

# --- Data and Model Loading ---
@st.cache_data
def load_data_and_models():
    try:
        model = joblib.load('type_classifier_model.pkl')
        vectorizer = joblib.load('tfidf_type_vectorizer.pkl')
        
        current_dir = os.path.dirname(__file__)
        parent_dir = os.path.join(current_dir, '..')
        data_path = os.path.join(parent_dir, 'processed_data_for_dashboard.csv')
        df = pd.read_csv(data_path)
        return model, vectorizer, df, data_path
    except Exception as e:
        st.error(f"Error loading files. Please run _train_model.py first. Error: {e}")
        st.stop()
        
model, vectorizer, df_global, data_path_global = load_data_and_models()

# --- Data Update Function (Same) ---
def update_dashboard_data(df, new_status):
    if 'Ticket_#' in df.columns:
        max_ticket_num = pd.to_numeric(df['Ticket_#'], errors='coerce').max()
        new_ticket = int(max_ticket_num) + 1 if pd.notna(max_ticket_num) else len(df) + 1000
        new_ticket_str = str(new_ticket)
    else:
        new_ticket_str = str(len(df) + 1000)
    
    new_row = {
        'Customer_Complaint': st.session_state.current_complaint,
        'Complaint_Type': st.session_state.prediction,
        'Status_Group': new_status,
        'Ticket_#': new_ticket_str, 
        'Date': pd.to_datetime('today').strftime('%d-%m-%Y'),
        'Date_month_year': pd.to_datetime('today').strftime('%d-%b-%y'),
        'Time': pd.to_datetime('now').strftime('%I:%M:%S %p'),
        'Received_Via': 'Web AI',
        'City': 'Not Provided',
        'State': 'Not Provided',
        'Zip_code': 0,
        'Status': 'Solved' if new_status == 'Resolved' else 'Open',
        'Filing_on_Behalf_of_Someone': 'No',
        'Cleaned_Complaint': clean_text(st.session_state.current_complaint)
    }
    
    df_global.loc[len(df_global)] = new_row
    df_global.to_csv(data_path_global, index=False, encoding='utf-8')

# --- UI Setup ---
st.markdown("# 👤 Agent Mode: Smart Complaint Resolution System")
st.markdown("---")

# Initialize Session State
if 'analysis_done' not in st.session_state: st.session_state.analysis_done = False
if 'current_complaint' not in st.session_state: st.session_state.current_complaint = ""
if 'show_escalation_form' not in st.session_state: st.session_state.show_escalation_form = False
if 'show_submission_page' not in st.session_state: st.session_state.show_submission_page = False
if 'last_action_status' not in st.session_state: st.session_state.last_action_status = ""


# ----------------- FINAL SUBMISSION PAGE (TOP SECTION) -----------------
if st.session_state.show_submission_page:
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    if st.session_state.last_action_status == "Resolved":
        color = "#2ECC71" # Green
        icon = "✅"
        title = "SUCCESS: ISSUE RESOLVED AND CLOSED"
        message = "Thank you for the swift action! Your issue has been marked as **RESOLVED** and a confirmation has been sent to your customer."
    else:
        color = "#E74C3C" # Red
        icon = "🚨"
        title = "ESCALATION SUBMITTED TO TIER 2"
        message = "The case requires further managerial attention. **All submitted details have been forwarded** to the Manager Queue for follow-up."

    # Custom Submission Box
    with st.container(border=True):
        st.markdown(f"""
            <div style="background-color: {color}; padding: 15px; border-radius: 5px; color: white;">
                <h2 style='margin: 0;'>{icon} {title}</h2>
            </div>
            <div style="padding: 20px;">
                <p style='font-size: 18px;'>{message}</p>
                <p style='color: #888;'>*Agent Note: Manager dashboard has been updated.*</p>
            </div>
            """, unsafe_allow_html=True)
            
    st.markdown("---")
    if st.button("➕ Start New Complaint Analysis", key='new_comp_btn', type="primary"):
        st.session_state.show_submission_page = False
        st.session_state.analysis_done = False
        st.session_state.current_complaint = ""
        st.rerun() 
    st.stop() # Execution stop here


# ----------------- INPUT AREA (MAIN LOGIC) -----------------

# --- Input Box and Analyze Button ---
if not st.session_state.analysis_done: # Only show input area if analysis hasn't been run
    complaint_text = st.text_area("Enter Customer Complaint Here:", 
                                  "My internet has been very slow since yesterday and the support team was rude when I called.",
                                  height=150, key="complaint_input")
    
    if st.button("Analyze Complaint & Suggest Tier 1 Action", key='analyze_btn', type="primary"):
        if complaint_text:
            # Analysis Logic
            cleaned_input = clean_text(complaint_text)
            input_vectorized = vectorizer.transform([cleaned_input])
            prediction = model.predict(input_vectorized)[0]
            sentiment, emoji = analyze_sentiment(complaint_text)
            
            st.session_state.prediction = prediction
            st.session_state.sentiment = sentiment
            st.session_state.sentiment_emoji = emoji
            st.session_state.analysis_done = True
            st.session_state.current_complaint = complaint_text
            st.session_state.show_escalation_form = False
            
            st.rerun() 
        else:
            st.warning("Please enter the complaint text.")


# ----------------- Dynamic Resolution Flow (Post-Analysis) -----------------
if st.session_state.analysis_done:
    
    current_prediction = st.session_state.prediction
    current_sentiment = st.session_state.sentiment
    current_emoji = st.session_state.sentiment_emoji
    
    st.markdown("---")
    
    # --- AI ANALYSIS CARD (TOP ROW) ---
    st.subheader("1. AI Diagnostic and Status")
    
    with st.container(border=True): # Card 1
        colA, colB, colC = st.columns([1, 1, 1])
        
        mood_color = 'red' if current_sentiment == 'Negative' else ('orange' if current_sentiment == 'Neutral' else 'green')
        priority_level = "🔴 HIGH" if current_sentiment == 'Negative' else "🟡 MEDIUM"
        
        with colA:
            st.metric("Predicted Issue Type", current_prediction, delta_color="off")
        with colB:
            st.markdown(f"**Customer Mood:** :**{mood_color}[{current_sentiment}]** {current_emoji}")
        with colC:
            st.metric("Priority Level", priority_level, delta_color="off")


    # --- TIER 1 SUGGESTION (CONTEXTUAL RESPONSE) ---
    if 'Speed' in current_prediction or 'Network' in current_prediction:
        suggestion_text = "The system suggests asking the customer to **Restart their modem/router** and initiating a **System Diagnostic** to resolve basic connectivity issues."
        agent_line = "Sir/Ma'am, I understand the frustration. We are initiating a line diagnostic immediately. Can you please try restarting your modem/router? This often resolves network speed issues."
        
    elif 'Billing' in current_prediction or 'Charges' in current_prediction:
        suggestion_text = "The system suggests immediately verifying the charges against the latest billing summary to pinpoint the error."
        agent_line = "Sir/Ma'am, I have pulled up your account. Let me immediately check the billing summary to pinpoint the exact source of the extra charge. We will ensure everything is accurate."
        
    elif 'Customer Service' in current_prediction:
        suggestion_text = "The system advises an immediate apology and flagging the case to Quality Assurance to handle the complaint with extreme care."
        agent_line = "Sir/Ma'am, I deeply apologize for the rude experience you faced. That is unacceptable. We are immediately flagging your case to the Quality Assurance team."
        
    else:
        suggestion_text = "The system suggests a standard account review to provide a quick answer based on past resolution data."
        agent_line = "Sir/Ma'am, thank you for providing the details. I will review your account history now to provide you with the fastest possible resolution."

    
    st.subheader("2. Suggested Resolution Path")
    
    with st.container(border=True):
        st.success(f"**AI Action Plan:** {suggestion_text}")
        st.info(f"**Agent's Suggested Response:** _{agent_line}_")


    # ----------------- FINAL ACTION BUTTONS & ESCALATION (BOTTOM ROW) -----------------
    st.markdown("#### Agent Action Confirmation:")
    
    if not st.session_state.show_escalation_form:
        
        col_res, col_esc_btn = st.columns([1, 3]) 

        with col_res:
            if st.button("✅ Solved & Closed (Tier 1)", key='solved_btn', type="primary", use_container_width=True):
                # Solved Logic
                update_dashboard_data(df_global, 'Resolved')
                
                st.session_state.last_action_status = "Resolved"
                st.session_state.show_submission_page = True 
                st.rerun() 

        with col_esc_btn:
            if st.button("❌ Requires Escalation (Tier 2/Manager)", key='escalate_btn', type="secondary"):
                # Escalation Form Toggle Logic
                st.session_state.show_escalation_form = True
                st.rerun() # Rerun to show the form


# --- ESCALATION FORM ---
if st.session_state.show_escalation_form:
    st.markdown("---")
    
    with st.expander("🚨 ESCALATION DETAILS FORM", expanded=True): # Card 3
        st.warning(f"Customer's mood is **{st.session_state.sentiment} {st.session_state.sentiment_emoji}**. Please collect details to forward to the Manager.")
        
        with st.form("escalation_form"):
            escalation_name = st.text_input("Customer Name", placeholder="e.g., John Smith")
            escalation_email = st.text_input("Contact Email", placeholder="e.g., customer@example.com")
            escalation_phone = st.text_input("Contact Phone Number", placeholder="e.g., +1 555-555-1234")
            
            submitted = st.form_submit_button("Submit Escalation to Manager", type="primary")

            if submitted:
                if not escalation_name or not escalation_email or not escalation_phone:
                    st.error("Please fill in all required contact details.")
                else:
                    # Escalation Submission Logic
                    update_dashboard_data(df_global, 'Unresolved') # Log as Unresolved for now
                    
                    st.session_state.last_action_status = "Unresolved"
                    st.session_state.show_submission_page = True
                    st.rerun()


st.markdown("---")
st.caption("This professional demo utilizes AI Classification, Sentiment, and a Multi-Tier Resolution Flow.")