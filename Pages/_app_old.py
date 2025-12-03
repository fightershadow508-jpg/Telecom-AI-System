import streamlit as st
import joblib
import re

# Model aur Vectorizer ko load karein
try:
    # FILES HUMARE PASS train_model.py run karne ke baad ban gayi hain
    model = joblib.load('log_reg_resolution_model.pkl')
    tfidf_vectorizer = joblib.load('tfidf_vectorizer.pkl')
    model_loaded = True
except FileNotFoundError:
    st.error("Model files load nahi ho sake. Pehle train_model.py run karein.")
    model_loaded = False

# Function: Text Cleaning
def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    return text

# Streamlit App Title
st.title("🤖 AI Complaint Resolution System (POC)")
st.subheader("Supervisor Demo: Complaint Status Prediction")

if model_loaded:
    # Text Input box
    complaint_text = st.text_area("Customer Complaint Yahan Likhye:", 
                                  "Meri internet speed bahut slow hai aur service baar baar disconnect ho rahi hai.")

    # Prediction Button
    if st.button("Complaint Status Predict Karein"):
        if complaint_text:
            cleaned_input = clean_text(complaint_text)
            input_vectorized = tfidf_vectorizer.transform([cleaned_input])
            
            prediction = model.predict(input_vectorized)
            probability = model.predict_proba(input_vectorized)
            
            st.markdown("---")
            st.subheader("⚡ Prediction Result:")

            if prediction[0] == 1:
                st.success(f"**AI Prediction:** 🟢 RESOLVED")
                st.write(f"Is complaint ke **Solved** hone ki sambhavna hai: **{probability[0][1]*100:.2f}%**")
            else:
                st.warning(f"**AI Prediction:** 🔴 UNRESOLVED")
                st.write(f"Is complaint ke **Unresolved** rehne ki sambhavna hai: **{probability[0][0]*100:.2f}%**")
        else:
            st.warning("Please complaint text darj karein.")

st.markdown("---")
st.caption("Yeh system complaint text ko analyse karke resolution status predict karta hai.")