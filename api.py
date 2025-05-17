from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from typing import List, Optional
from bson import ObjectId
from datetime import datetime

from auth import (
    authenticate_user, create_access_token, get_current_active_user,
    get_password_hash, Token, ACCESS_TOKEN_EXPIRE_MINUTES
)
from database import (
    create_user, get_user_emails, get_email_count, get_email_by_id
)
from models import (
    UserCreate, UserResponse, EmailFilter, EmailCreate, 
    EmailResponse, EmailFetchRequest, PaginationParams
)
from email_utils import fetch_emails, send_email

app = FastAPI(title="Email Documentation API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate):
    """Register a new user"""
    # Check if user already exists
    from database import get_user_by_email
    existing_user = get_user_by_email(user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    hashed_password = get_password_hash(user.password)
    user_data = {
        "email": user.email,
        "hashed_password": hashed_password,
        "full_name": user.full_name,
        "created_at": datetime.now(),
        "disabled": False
    }
    
    result = create_user(user_data)
    user_data["id"] = str(result.inserted_id)
    
    return UserResponse(
        id=user_data["id"],
        email=user_data["email"],
        full_name=user_data["full_name"],
        created_at=user_data["created_at"]
    )

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Get access token"""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user = Depends(get_current_active_user)):
    """Get current user information"""
    return UserResponse(
        id=str(current_user["_id"]),
        email=current_user["email"],
        full_name=current_user.get("full_name"),
        created_at=current_user.get("created_at")
    )

@app.post("/emails/fetch")
async def fetch_user_emails(
    request: EmailFetchRequest,
    current_user = Depends(get_current_active_user)
):
    """Fetch emails from IMAP server"""
    emails = fetch_emails(
        user_id=current_user["_id"],
        email_address=request.email_address,
        password=request.password,
        folder=request.folder,
        limit=request.limit
    )
    
    return {"message": f"Successfully fetched {len(emails)} emails", "count": len(emails)}

@app.get("/emails", response_model=List[EmailResponse])
async def get_emails(
    pagination: PaginationParams = Depends(),
    subject: Optional[str] = None,
    sender: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user = Depends(get_current_active_user)
):
    """Get user emails with pagination and filtering"""
    filters = {}
    if subject:
        filters["subject"] = subject
    if sender:
        filters["sender"] = sender
    if date_from and date_to:
        from datetime import datetime
        filters["date_from"] = datetime.fromisoformat(date_from)
        filters["date_to"] = datetime.fromisoformat(date_to)
    
    emails = get_user_emails(
        user_id=ObjectId(current_user["_id"]),
        skip=pagination.skip,
        limit=pagination.limit,
        filters=filters
    )
    
    total_count = get_email_count(
        user_id=ObjectId(current_user["_id"]),
        filters=filters
    )
    
    # Convert ObjectId to string for JSON serialization
    for email in emails:
        email["id"] = str(email["_id"])
        email["_id"] = str(email["_id"])
        email["user_id"] = str(email["user_id"])
    
    return emails

@app.get("/emails/{email_id}", response_model=EmailResponse)
async def get_email(
    email_id: str,
    current_user = Depends(get_current_active_user)
):
    """Get email by ID"""
    try:
        email = get_email_by_id(ObjectId(email_id))
        if not email:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email not found"
            )
        
        # Check if email belongs to current user
        if str(email["user_id"]) != current_user["_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this email"
            )
        
        # Convert ObjectId to string for JSON serialization
        email["id"] = str(email["_id"])
        email["_id"] = str(email["_id"])
        email["user_id"] = str(email["user_id"])
        
        return email
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid email ID: {str(e)}"
        )

@app.post("/emails/send")
async def send_new_email(
    email_data: EmailCreate,
    current_user = Depends(get_current_active_user)
):
    """Send a new email"""
    from config import EMAIL_USERNAME, EMAIL_PASSWORD
    
    result = send_email(
        sender=EMAIL_USERNAME,
        password=EMAIL_PASSWORD,
        recipient=email_data.recipient,
        subject=email_data.subject,
        body=email_data.body,
        html_body=email_data.html_body
    )
    
    if result:
        return {"message": "Email sent successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send email"
        )