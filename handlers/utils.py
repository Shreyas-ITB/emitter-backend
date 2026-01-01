import bcrypt
from hashlib import sha256

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def generate_profile_picture(username: str) -> str:
    # Generate a unique profile picture URL (you can replace this with Gravatar or other services)
    return f"https://robohash.org/{sha256(username.encode()).hexdigest()}.png"
