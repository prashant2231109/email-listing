import streamlit as st 
import requests
import json
from datetime import datetime, timedelta
import pandas as pd


API_URL = "http://localhost:8000"


st.set_page_config(
    page_title="Email Documentation System",
    page_icon="📧",
    layout="wide"
)


if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "login"
if "emails" not in st.session_state:
    st.session_state.emails = []
if "selected_email" not in st.session_state:
    st.session_state.selected_email = None
if "email_count" not in st.session_state:
    st.session_state.email_count = 0
if "page" not in st.session_state:
    st.session_state.page = 0
if "filters" not in st.session_state:
    st.session_state.filters = {}


def register_user(email, password, full_name):
    """Register a new user"""
    try:
        response = requests.post(
            f"{API_URL}/register",
            json={"email": email, "password": password, "full_name": full_name}
        )
        if response.status_code == 200:
            return True, "Registration successful! Please login."
        else:
            return False, f"Registration failed: {response.json().get('detail', 'Unknown error')}"
    except Exception as e:
        return False, f"Registration failed: {str(e)}"

def login_user(email, password):
    """Login user and get access token"""
    try:
        response = requests.post(
            f"{API_URL}/token",
            data={"username": email, "password": password}
        )
        if response.status_code == 200:
            token_data = response.json()
            st.session_state.token = token_data["access_token"]
           
            user_response = requests.get(
                f"{API_URL}/users/me",
                headers={"Authorization": f"Bearer {st.session_state.token}"}
            )
            if user_response.status_code == 200:
                st.session_state.user = user_response.json()
                return True, "Login successful!"
            else:
                st.session_state.token = None
                return False, "Failed to get user information"
        else:
            return False, f"Login failed: {response.json().get('detail', 'Unknown error')}"
    except Exception as e:
        return False, f"Login failed: {str(e)}"

def fetch_emails(email_address, password, folder="INBOX", limit=10):
    """Fetch emails from IMAP server"""
    try:
        response = requests.post(
            f"{API_URL}/emails/fetch",
            json={"email_address": email_address, "password": password, "folder": folder, "limit": limit},
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        if response.status_code == 200:
            return True, response.json().get("message", "Emails fetched successfully")
        else:
            return False, f"Failed to fetch emails: {response.json().get('detail', 'Unknown error')}"
    except Exception as e:
        return False, f"Failed to fetch emails: {str(e)}"

def get_emails(skip=0, limit=20, filters=None):
    """Get emails with pagination and filtering"""
    try:
        params = {"skip": skip, "limit": limit}
        if filters:
            params.update(filters)
        
        response = requests.get(
            f"{API_URL}/emails",
            params=params,
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to get emails: {response.json().get('detail', 'Unknown error')}")
            return []
    except Exception as e:
        st.error(f"Failed to get emails: {str(e)}")
        return []

def get_email(email_id):
    """Get email by ID"""
    try:
        response = requests.get(
            f"{API_URL}/emails/{email_id}",
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to get email: {response.json().get('detail', 'Unknown error')}")
            return None
    except Exception as e:
        st.error(f"Failed to get email: {str(e)}")
        return None

def send_email(recipient, subject, body, html_body=None):
    """Send a new email"""
    try:
        response = requests.post(
            f"{API_URL}/emails/send",
            json={"recipient": recipient, "subject": subject, "body": body, "html_body": html_body},
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        if response.status_code == 200:
            return True, "Email sent successfully"
        else:
            return False, f"Failed to send email: {response.json().get('detail', 'Unknown error')}"
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"

def logout():
    """Logout user"""
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.current_page = "login"
    st.session_state.emails = []
    st.session_state.selected_email = None
    st.session_state.email_count = 0
    st.session_state.page = 0
    st.session_state.filters = {}


def login_page():
    """Login page"""
    st.title("📧 Email Documentation System")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if email and password:
                    success, message = login_user(email, password)
                    if success:
                        st.success(message)
                        st.session_state.current_page = "dashboard"
                        st.experimental_rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Please enter email and password")
    
    with tab2:
        with st.form("register_form"):
            full_name = st.text_input("Full Name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            st.markdown("---")
            st.markdown("If you'd like to receive helpful onboarding emails, news, offers, promotions, "
                      "and the occasional swag, please enter your email address below. Otherwise, "
                      "leave this field blank.")
            newsletter_email = st.text_input("Email for newsletter (optional)")
            
            submit = st.form_submit_button("Register")
            
            if submit:
                if email and password and confirm_password:
                    if password != confirm_password:
                        st.error("Passwords do not match")
                    else:
                        success, message = register_user(email, password, full_name)
                        if success:
                            st.success(message)
                            if newsletter_email:
                                st.success(f"You've been subscribed to our newsletter at {newsletter_email}")
                        else:
                            st.error(message)
                else:
                    st.error("Please fill all required fields")

def sidebar():
    """Sidebar navigation"""
    st.sidebar.title(f"Welcome, {st.session_state.user.get('full_name', st.session_state.user.get('email'))}")
    
    st.sidebar.markdown("### Navigation")
    if st.sidebar.button("📊 Dashboard"):
        st.session_state.current_page = "dashboard"
        st.experimental_rerun()
    
    if st.sidebar.button("📥 Fetch Emails"):
        st.session_state.current_page = "fetch_emails"
        st.experimental_rerun()
    
    if st.sidebar.button("📧 View Emails"):
        st.session_state.current_page = "view_emails"
        st.session_state.emails = get_emails(skip=0, limit=20)
        st.experimental_rerun()
    
    if st.sidebar.button("✉️ Compose Email"):
        st.session_state.current_page = "compose_email"
        st.experimental_rerun()
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout"):
        logout()
        st.experimental_rerun()

def dashboard_page():
    """Dashboard page"""
    st.title("📊 Dashboard")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Quick Actions")
        if st.button("📥 Fetch New Emails"):
            st.session_state.current_page = "fetch_emails"
            st.experimental_rerun()
            
        if st.button("✉️ Compose New Email"):
            st.session_state.current_page = "compose_email"
            st.experimental_rerun()
    
    with col2:
        st.subheader("User Information")
        st.write(f"**Email:** {st.session_state.user.get('email')}")
        st.write(f"**Name:** {st.session_state.user.get('full_name', 'Not provided')}")

def fetch_emails_page():
    """Fetch emails page"""
    st.title("📥 Fetch Emails")
    
    with st.form("fetch_emails_form"):
        email_address = st.text_input("Email Address")
        password = st.text_input("Password", type="password")
        folder = st.selectbox("Folder", ["INBOX", "Sent", "Drafts", "Trash", "Spam"])
        limit = st.slider("Number of emails to fetch", min_value=5, max_value=50, value=10)
        submit = st.form_submit_button("Fetch Emails")
        
        if submit:
            if email_address and password:
                with st.spinner("Fetching emails..."):
                    success, message = fetch_emails(email_address, password, folder, limit)
                    if success:
                        st.success(message)
                        st.session_state.current_page = "view_emails"
                        st.session_state.emails = get_emails(skip=0, limit=20)
                        st.experimental_rerun()
                    else:
                        st.error(message)
            else:
                st.error("Please enter email address and password")

def view_emails_page():
    """View emails page"""
    st.title("📧 Email Inbox")
    
    if not st.session_state.emails:
        st.info("No emails found. Try fetching emails first.")
    else:
        emails_df = pd.DataFrame([
            {"Subject": email.get("subject"), "Sender": email.get("sender"), "Date": email.get("date")}
            for email in st.session_state.emails
        ])
        st.dataframe(emails_df)
        
        email_id = st.selectbox(
            "Select an email to view",
            options=[email.get("id") for email in st.session_state.emails],
            format_func=lambda x: next((email.get("subject") for email in st.session_state.emails if email.get("id") == x), "")
        )
        
        if email_id and st.button("View Email"):
            st.session_state.selected_email = get_email(email_id)
            if st.session_state.selected_email:
                st.session_state.current_page = "view_email"
                st.experimental_rerun()

def view_email_page():
    """View single email page"""
    if not st.session_state.selected_email:
        st.error("No email selected")
        st.session_state.current_page = "view_emails"
        st.experimental_rerun()
    
    email = st.session_state.selected_email
    st.title(email.get("subject", "No Subject"))
    st.write(f"**From:** {email.get('sender', 'Unknown')}")
    st.write(f"**Date:** {email.get('date', 'Unknown')}")
    st.markdown("---")
    st.markdown(email.get("body", "No content"))
    
    if st.button("Back to Emails"):
        st.session_state.current_page = "view_emails"
        st.experimental_rerun()

def compose_email_page():
    """Compose email page"""
    st.title("✉️ Compose Email")
    
    with st.form("compose_email_form"):
        recipient = st.text_input("To")
        subject = st.text_input("Subject")
        body = st.text_area("Message", height=300)
        submit = st.form_submit_button("Send Email")
        
        if submit:
            if recipient and subject and body:
                with st.spinner("Sending email..."):
                    success, message = send_email(recipient, subject, body)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
            else:
                st.error("Please fill all required fields")

def main():
    if st.session_state.token is None:
        login_page()
    else:
        sidebar()
        
        if st.session_state.current_page == "dashboard":
            dashboard_page()
        elif st.session_state.current_page == "fetch_emails":
            fetch_emails_page()
        elif st.session_state.current_page == "view_emails":
            view_emails_page()
        elif st.session_state.current_page == "view_email":
            view_email_page()
        elif st.session_state.current_page == "compose_email":
            compose_email_page()
        else:
            dashboard_page()

if __name__ == "__main__":
    main()