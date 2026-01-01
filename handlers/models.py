from pymongo import IndexModel, ASCENDING
from handlers.config import user_collection

# Create indexes for email and username
user_collection.create_indexes([
    IndexModel([("email", ASCENDING)], unique=True),
    IndexModel([("username", ASCENDING)], unique=True),
])