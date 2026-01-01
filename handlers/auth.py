import uuid
from datetime import datetime, timedelta
from jose import jwt, JWTError
from authlib.integrations.starlette_client import OAuth
from handlers.config import (
    GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET,
    GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET,
    APPLE_CLIENT_ID, DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET, EXPIRATION_MINUTES, SECRET_KEY, ALGORITHM
)

oauth = OAuth()

# Register Google OAuth
oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# Register GitHub OAuth
oauth.register(
    name='github',
    client_id=GITHUB_CLIENT_ID,
    client_secret=GITHUB_CLIENT_SECRET,
    authorize_url='https://github.com/login/oauth/authorize',
    access_token_url='https://github.com/login/oauth/access_token',
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'user:email'}
)

# Register Apple OAuth
oauth.register(
    name='apple',
    client_id=APPLE_CLIENT_ID,
    client_secret=None,  # Apple client secret will be dynamically generated
    authorize_url='https://appleid.apple.com/auth/authorize',
    access_token_url='https://appleid.apple.com/auth/token',
    client_kwargs={'scope': 'openid email'}
)

oauth.register(
    name='discord',
    client_id=DISCORD_CLIENT_ID,
    client_secret=DISCORD_CLIENT_SECRET,
    authorize_url='https://discord.com/api/oauth2/authorize',
    access_token_url='https://discord.com/api/oauth2/token',
    api_base_url='https://discord.com/api/',
    client_kwargs={'scope': 'identify email'}
)

def create_verification_code():
    """
    Generates a unique verification code (UUID) with an associated timestamp.
    Returns:
    - A dictionary containing the verification code and its expiration time.
    """
    verification_code = str(uuid.uuid4())
    expiration_time = datetime.utcnow() + timedelta(minutes=EXPIRATION_MINUTES)
    return {"code": verification_code, "expires_at": expiration_time}

async def verify_verification_code(verification_code: str, db_collection):
    """
    Verifies the provided verification code by checking the database and its expiration.
    
    Args:
    - verification_code: The unique code sent to the user's email.
    - db_collection: The MongoDB collection where user data is stored.
    
    Returns:
    - User document if the verification code is valid and not expired.
    - None if the verification code is invalid or expired.
    """
    user = await db_collection.find_one({"verification_code.code": verification_code})
    if not user:
        return None

    expiration_time = user["verification_code"]["expires_at"]
    if datetime.utcnow() > expiration_time:
        return None  # Verification code expired

    return user

def create_access_token(data: dict, expires_delta: timedelta) -> str:
    """Creates a JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_jwt(token: str) -> dict:
    try:
        # Decode the JWT and return the payload
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None