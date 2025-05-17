# Email Documentation System

A complete email documentation system with Streamlit frontend, FastAPI backend, MongoDB database, and IMAP/SMTP email functionality.

## Features

- User authentication and registration
- Email fetching from IMAP servers
- Email sending via SMTP
- Email filtering and search
- Email viewing and organization
- Responsive UI with Streamlit

## Quick Start

### Run the Frontend

Double-click on `run_frontend.bat` to start the Streamlit frontend.

### MongoDB Note

The system will automatically use in-memory storage if MongoDB is not available. For persistent storage, install MongoDB and make sure it's running on localhost:27017.

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and update the values:

```bash
cp .env.example .env
```

Edit the `.env` file with your MongoDB connection string, JWT secret key, and email credentials.

### 3. Start the Backend

```bash
python main.py
```

This will start the FastAPI backend on http://localhost:8000.

### 4. Start the Frontend

```bash
streamlit run frontend.py
```

This will start the Streamlit frontend on http://localhost:8501.

## MongoDB Setup (Optional)

1. Install MongoDB from https://www.mongodb.com/try/download/community
2. Start MongoDB service
3. The application will automatically connect to MongoDB if available

## Email Configuration

For Gmail:
- Enable "Less secure app access" or use App Passwords
- Set `EMAIL_HOST` to "smtp.gmail.com"
- Set `EMAIL_PORT` to 587
- Set `IMAP_SERVER` to "imap.gmail.com"
- Set `IMAP_PORT` to 993