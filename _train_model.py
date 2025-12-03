import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import joblib
import re
import os # <-- Zaroori: File Path check karne ke liye

FILE_NAME = "Comcast_telecom_complaints_data.csv"

# 1. Data Cleaning
df = pd.read_csv(FILE_NAME)
df.columns = df.columns.str.replace(' ', '_')
df['Customer_Complaint'] = df['Customer_Complaint'].astype(str)

# Function to extract major category
def get_complaint_type(text):
    text = text.lower()
    if 'bill' in text or 'charge' in text or 'fee' in text or 'pricing' in text:
        return 'Billing/Charges'
    elif 'speed' in text or 'slow' in text or 'throttle' in text:
        return 'Internet Speed'
    elif 'service' in text or 'disconnected' in text or 'network' in text or 'outage' in text:
        return 'Service/Network'
    elif 'support' in text or 'rude' in text or 'customer' in text or 'contact' in text:
        return 'Customer Service'
    else:
        return 'Other/Technical'

df['Complaint_Type'] = df['Customer_Complaint'].apply(get_complaint_type)

# Simplify Status for Manager Dashboard (Resolved vs Unresolved)
df['Status_Group'] = df['Status'].apply(lambda x: 'Resolved' if 'Solved' in x else 'Unresolved')

# 2. Text Preprocessing Function
def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text) 
    return text

df['Cleaned_Complaint'] = df['Customer_Complaint'].apply(clean_text)

# 3. Classification Setup
X = df['Cleaned_Complaint']
y = df['Complaint_Type']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 4. TF-IDF and Model Training
tfidf_vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
X_train_tfidf = tfidf_vectorizer.fit_transform(X_train)

model = LogisticRegression(max_iter=1000)
model.fit(X_train_tfidf, y_train)

# 5. Saving all necessary files
joblib.dump(model, 'type_classifier_model.pkl')
joblib.dump(tfidf_vectorizer, 'tfidf_type_vectorizer.pkl')

# --- FINAL FILE SAVING FIX (100% Guaranteed) ---
# Current Working Directory check
current_path = os.getcwd()
print(f"File saving location is: {current_path}") 

# Saving the processed DataFrame for the Manager Dashboard with encoding fix
df.to_csv('processed_data_for_dashboard.csv', index=False, encoding='utf-8')
print("✅ All necessary files (Model, Vectorizer, Data) saved successfully.")