from pymongo import MongoClient
from config import MONGO_URI, DB_NAME
import os
import json
from datetime import datetime
from bson import ObjectId


in_memory_db = {
    "users": [],
    "emails": []
}


class MongoJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


try:
   
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
   
    client.server_info()
    db = client[DB_NAME]
    
    
    users_collection = db["users"]
    emails_collection = db["emails"]
    
    
    users_collection.create_index("email", unique=True)
    emails_collection.create_index("user_id")
    emails_collection.create_index("date")
    
    print("Connected to MongoDB successfully")
    USE_MONGO = True
    
except Exception as e:
    print(f"MongoDB connection failed: {str(e)}")
    print("Using in-memory storage instead")
    USE_MONGO = False

def get_user_by_email(email: str):
    """Get user by email"""
    if USE_MONGO:
        return users_collection.find_one({"email": email})
    else:
        for user in in_memory_db["users"]:
            if user["email"] == email:
                return user
        return None

def create_user(user_data: dict):
    """Create a new user"""
    if USE_MONGO:
        return users_collection.insert_one(user_data)
    else:
        
        for user in in_memory_db["users"]:
            if user["email"] == user_data["email"]:
                raise Exception("Email already exists")
        
        
        user_data["_id"] = ObjectId()
        in_memory_db["users"].append(user_data)
        
        class Result:
            def __init__(self, id):
                self.inserted_id = id
        
        return Result(user_data["_id"])

def update_user(user_id, update_data: dict):
    """Update user information"""
    if USE_MONGO:
        return users_collection.update_one({"_id": user_id}, {"$set": update_data})
    else:
        for i, user in enumerate(in_memory_db["users"]):
            if user["_id"] == user_id:
                in_memory_db["users"][i].update(update_data)
                return True
        return False

def save_email(email_data: dict):
    """Save email to database"""
    if USE_MONGO:
        return emails_collection.insert_one(email_data)
    else:
        
        email_data["_id"] = ObjectId()
        in_memory_db["emails"].append(email_data)
        
        class Result:
            def __init__(self, id):
                self.inserted_id = id
        
        return Result(email_data["_id"])

def get_user_emails(user_id, skip=0, limit=20, filters=None):
    """Get emails for a specific user with pagination and optional filters"""
    if USE_MONGO:
        query = {"user_id": user_id}
        
        if filters:
            if filters.get("subject"):
                query["subject"] = {"$regex": filters["subject"], "$options": "i"}
            if filters.get("sender"):
                query["sender"] = {"$regex": filters["sender"], "$options": "i"}
            if filters.get("date_from") and filters.get("date_to"):
                query["date"] = {"$gte": filters["date_from"], "$lte": filters["date_to"]}
        
        return list(emails_collection.find(query).sort("date", -1).skip(skip).limit(limit))
    else:
        
        filtered_emails = []
        for email in in_memory_db["emails"]:
            if email["user_id"] == user_id:
                include = True
                
                if filters:
                    if filters.get("subject") and filters["subject"].lower() not in email["subject"].lower():
                        include = False
                    if filters.get("sender") and filters["sender"].lower() not in email["sender"].lower():
                        include = False
                    if filters.get("date_from") and filters.get("date_to"):
                        if email["date"] < filters["date_from"] or email["date"] > filters["date_to"]:
                            include = False
                
                if include:
                    filtered_emails.append(email)
        
        
        filtered_emails.sort(key=lambda x: x["date"], reverse=True)
        
        
        return filtered_emails[skip:skip+limit]

def get_email_count(user_id, filters=None):
    """Get count of emails for a specific user with optional filters"""
    if USE_MONGO:
        query = {"user_id": user_id}
        
        if filters:
            if filters.get("subject"):
                query["subject"] = {"$regex": filters["subject"], "$options": "i"}
            if filters.get("sender"):
                query["sender"] = {"$regex": filters["sender"], "$options": "i"}
            if filters.get("date_from") and filters.get("date_to"):
                query["date"] = {"$gte": filters["date_from"], "$lte": filters["date_to"]}
        
        return emails_collection.count_documents(query)
    else:
        
        return len(get_user_emails(user_id, 0, 9999, filters))

def get_email_by_id(email_id):
    """Get email by ID"""
    if USE_MONGO:
        return emails_collection.find_one({"_id": email_id})
    else:
        for email in in_memory_db["emails"]:
            if email["_id"] == email_id:
                return email
        return None