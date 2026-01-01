from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request, Response, UploadFile
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import StreamingResponse
from slowapi.errors import RateLimitExceeded
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from handlers.schemas import (UserSignup, UserLogin, ResendVerificationRequest, Interests, PostCreateSchema, PostEditSchema, PostDeleteSchema, PostGetSchema, RoleAssignSchema, RoleDeleteSchema, RoleEditSchema, CommunityDeleteSchema, CommunityModerationSchema, ReportClearSchema,
CommentCreateSchema, CommentDeleteSchema, CommentDislikeSchema, CommentEditSchema, CommentLikeSchema, CommentReportSchema, PostReportSchema, CommunityCreateSchema, RoleCreateSchema, CommunityActionSchema, CommunityReportSchema, HandleSchema, BioSchema, FollowUnfollowSchema, CommunityPostsSchema,
AlgorithmRecommendCommunitySchema, AlgorithmRecommendPostsSchema, AlgorithmRecommendUsersSchema, RoleGiveSchema, SocialLinksSchema, PronounsSchema, ChatRequestSchema)
from generators.gen_post_info import process_post
from generators.spam_model import classify
from handlers.utils import hash_password, verify_password, generate_profile_picture
from handlers.email_sender import send_verification_email, send_warn_email, send_ban_email
from handlers.auth import create_verification_code, verify_verification_code, create_access_token, decode_jwt, oauth
from handlers.config import user_collection, reports_collection, communities_collection, banned_collection, all_subcategories, community_collection, read_posts_collection, SECRET_KEY, API_HOST, API_PORT, GOOGLE_REDIRECT_URI, GITHUB_REDIRECT_URI, DISCORD_REDIRECT_URI, APPLE_REDIRECT_URI, images_collection, posts_collection, TEAM_MEMBERS_HANDLES, MODEL_TO_USE
from generators.tagsystem import determine_tags
from datetime import datetime, timedelta, timezone
from algorithm.recommendation import recommend_content
from generators.sparkai import ChatSpark
from bson import ObjectId
from better_profanity import profanity
from PIL import Image
from typing import List
from uuid import uuid4
import io
import shutil
import re
import random
import string

app = FastAPI()
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
profanity.load_censor_words()
sparkai = ChatSpark(MODEL_TO_USE)

# async def validate_access_token(request: Request, response: Response):
#     """
#     Validates the access token from cookies. 
#     If the access token is invalid or expired, attempts to generate a new one using the refresh token.
#     If the refresh token is invalid or expired, raises an error.
#     """
#     access_token = request.cookies.get("token")
#     refresh_token = request.cookies.get("refresh_token")
#     if not access_token:
#         # If no access token is present, fall back to refresh token validation
#         if not refresh_token:
#             raise HTTPException(status_code=401, detail="Refresh token missing")

#         refresh_payload = decode_jwt(refresh_token)
#         if not refresh_payload:
#             raise HTTPException(status_code=401, detail="Invalid refresh token")

#         # Check if the refresh token is expired
#         refresh_exp_time = refresh_payload.get("exp")
#         if datetime.utcfromtimestamp(refresh_exp_time) < datetime.utcnow():
#             raise HTTPException(status_code=401, detail="Refresh token expired")

#         # Generate a new access token using the refresh token's user_id
#         user_id = refresh_payload.get("user_id")
#         new_access_token = create_access_token(
#             {"user_id": user_id}, expires_delta=timedelta(hours=2)
#         )

#         # Set the new access token in the cookies
#         response.set_cookie(key="token", value=new_access_token, httponly=True, secure=True)

#         # Decode the new access token to proceed
#         return decode_jwt(new_access_token)

#     # Decode the access token
#     access_payload = decode_jwt(access_token)
#     if not access_payload:
#         # Access token is invalid, check the refresh token
#         if not refresh_token:
#             raise HTTPException(status_code=401, detail="Refresh token missing")

#         refresh_payload = decode_jwt(refresh_token)
#         if not refresh_payload:
#             raise HTTPException(status_code=401, detail="Invalid refresh token")

#         # Check if the refresh token is expired
#         refresh_exp_time = refresh_payload.get("exp")
#         if datetime.utcfromtimestamp(refresh_exp_time) < datetime.utcnow():
#             raise HTTPException(status_code=401, detail="Refresh token expired")

#         # Generate a new access token using the refresh token's user_id
#         user_id = refresh_payload.get("user_id")
#         new_access_token = create_access_token(
#             {"user_id": user_id}, expires_delta=timedelta(hours=2)
#         )

#         # Set the new access token in the cookies
#         response.set_cookie(key="token", value=new_access_token, httponly=True, secure=True)

#         # Decode the new access token to proceed
#         return decode_jwt(new_access_token)

#     # Check access token expiration
#     access_exp_time = access_payload.get("exp")
#     if datetime.utcfromtimestamp(access_exp_time) < datetime.utcnow():
#         # Access token is expired, use the refresh token to generate a new one
#         if not refresh_token:
#             raise HTTPException(status_code=401, detail="Refresh token missing")

#         refresh_payload = decode_jwt(refresh_token)
#         if not refresh_payload:
#             raise HTTPException(status_code=401, detail="Invalid refresh token")

#         # Check if the refresh token is expired
#         refresh_exp_time = refresh_payload.get("exp")
#         if datetime.utcfromtimestamp(refresh_exp_time) < datetime.utcnow():
#             raise HTTPException(status_code=401, detail="Refresh token expired")

#         # Generate a new access token
#         user_id = refresh_payload.get("user_id")
#         new_access_token = create_access_token(
#             {"user_id": user_id}, expires_delta=timedelta(hours=2)
#         )

#         # Set the new access token in the cookies
#         response.set_cookie(key="token", value=new_access_token, httponly=True, secure=True)

#         # Decode the new access token to proceed
#         return decode_jwt(new_access_token)

#     # Return the valid access token payload
#     return access_payload

async def validate_access_token(request: Request):
    """
    Validates the access token from cookies.
    If valid, returns the decoded payload.
    If invalid or expired, raises an error.
    """
    access_token = request.cookies.get("token")

    if not access_token:
        raise HTTPException(status_code=401, detail="Access token missing")

    # Decode the access token
    access_payload = decode_jwt(access_token)

    if not access_payload:
        raise HTTPException(status_code=401, detail="Invalid access token")

    # Check if the access token is expired
    access_exp_time = access_payload.get("exp")
    if datetime.utcfromtimestamp(access_exp_time) < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Access token expired")

    # If the token is valid, return the payload
    return access_payload

# Helper function to validate tags
def validate_tags(tags: List[str]):
    for tag in tags:
        if profanity.contains_profanity(tag):
            raise HTTPException(status_code=400, detail=f"Tag '{tag}' contains inappropriate language and is not allowed.")

async def process_uploaded_image_file(image: UploadFile) -> str:
    # Validate file size (under 15 MB)
    if await image.readable():
        image.file.seek(0, 2)  # Move to end of file
        file_size = image.file.tell()
        image.file.seek(0)  # Reset pointer to start
        if file_size > 15 * 1024 * 1024:  # 15 MB
            raise HTTPException(status_code=400, detail="Image size exceeds 15MB")

    # Read the image as bytes and save in the database
    image_data = await image.read()
    image_document = {"data": image_data}
    result = await images_collection.insert_one(image_document)

    # Return the image's unique ID as a URL endpoint
    return f"/images/{result.inserted_id}"

@app.post("/signup")
async def signup(user: UserSignup, background_tasks: BackgroundTasks):
    banned_user = await banned_collection.find_one({"email": user.email})
    if banned_user:
        raise HTTPException(
            status_code=403,
            detail="This email has been banned from the platform.")
    # Check if the email already exists in the database
    existing_user = await user_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    profile_picture_data = None
    handle = user.handle.lower()

    # Validate the profile_picture field if provided
    if isinstance(user.profile_picture, UploadFile):
        # Check the file size (15 MB = 15 * 1024 * 1024 bytes)
        contents = await user.profile_picture.read()
        file_size = len(contents)
        if file_size > 15 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="File size exceeds the 15 MB limit.",
            )

        # Save the image to MongoDB
        try:
            # Convert to a PIL image and save as bytes
            image = Image.open(io.BytesIO(contents))
            image_bytes = io.BytesIO()
            image.save(image_bytes, format='JPEG')

            # Insert image into MongoDB
            profile_picture_data = {
                'data': image_bytes.getvalue()
            }
            profile_picture_id = images_collection.insert_one(profile_picture_data).inserted_id
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Error processing the uploaded image: {str(e)}"
            )
    
    if profanity.contains_profanity(user.bio):
        raise HTTPException(status_code=400, detail="Bio contains inappropriate language and is not allowed.")
        
    existing_user_by_handle = await user_collection.find_one({"handle": handle})
    if existing_user_by_handle:
        raise HTTPException(status_code=400, detail="Handle is already taken. Please choose a different one.")

    elif isinstance(user.profile_picture, str) and user.profile_picture:
        # If a URL is provided, validate it
        url_regex = re.compile(
            r"^(https?|ftp)://[^\s/$.?#].[^\s]*$", re.IGNORECASE
        )
        if not url_regex.match(user.profile_picture):
            raise HTTPException(
                status_code=400,
                detail="Invalid profile picture URL.",
            )
        profile_picture_data = {"url": user.profile_picture}

    else:
        # Generate a default profile picture if none is provided
        profile_picture_data = {"url": generate_profile_picture(user.username)}

    # Hash the user's password
    hashed_password = hash_password(user.password)

    # Create verification data
    verification_data = create_verification_code()

    # Construct the new user document
    new_user = {
        "username": user.username,
        "handle": handle,
        "bio": user.bio,
        "pronouns": user.pronouns,
        "badges": [],
        "email": user.email,
        "password": hashed_password,
        "interests": user.interests,
        "profile_picture": profile_picture_data,
        "is_verified": False,
        "verification_code": verification_data,  # Store code and expiration in the database
        "streak": 0,  # Initialize streak
        "lumens": 1,  # Initialize lumens
        "roles": [], # List of roles
        "followers": {
            "count": 0,  # Initialize with 0 followers
            "users": []  # Empty list of follower usernames
        },
        "following": {
            "count": 0,  # Initialize with 0 following
            "users": []  # Empty list of following usernames
        },
        "socials": user.socials,
        "last_streak_update": None,
        "posts_read_count": 0,
        "joined_on": datetime.utcnow()
    }

    # Insert the user into the database
    await user_collection.insert_one(new_user)

    # Send the verification email
    background_tasks.add_task(send_verification_email, user.email, verification_data["code"])

    return {"message": "User registered. Please verify your email."}

@app.get('/auth/google')
async def login_google(request: Request):
    return await oauth.google.authorize_redirect(request, GOOGLE_REDIRECT_URI)

@app.get('/auth/google/callback')
async def google_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get('userinfo')
    if not user_info:
        raise HTTPException(status_code=400, detail="Failed to fetch user info from Google")

    # Handle user info here (e.g., create or fetch user from DB)
    email = user_info['email']
    banned_user = await banned_collection.find_one({"email": email})
    if banned_user:
        raise HTTPException(
            status_code=403,
            detail="This email has been banned from the platform.")
    username = user_info.get('name')
    profile_picture = user_info.get('picture')

    user = await handle_oauth_user(email, username, profile_picture)
    return {"message": "Login successful", "user": user}

@app.get('/auth/github')
async def login_github(request: Request):
    return await oauth.github.authorize_redirect(request, GITHUB_REDIRECT_URI)

@app.get('/auth/github/callback')
async def github_callback(request: Request):
    token = await oauth.github.authorize_access_token(request)
    user_info = await oauth.github.get('user', token=token)
    user_info = user_info.json()
    if not user_info:
        raise HTTPException(status_code=400, detail="Failed to fetch user info from GitHub")

    email = user_info.get('email')
    banned_user = await banned_collection.find_one({"email": email})
    if banned_user:
        raise HTTPException(
            status_code=403,
            detail="This email has been banned from the platform.")
    username = user_info.get('login')
    profile_picture = user_info.get('avatar_url')

    user = await handle_oauth_user(email, username, profile_picture)
    return {"message": "Login successful", "user": user}

@app.get('/auth/apple')
async def login_apple(request: Request):
    return await oauth.apple.authorize_redirect(request, APPLE_REDIRECT_URI)

@app.get('/auth/apple/callback')
async def apple_callback(request: Request, response: Response):
    # Authorize the token from Apple
    token = await oauth.apple.authorize_access_token(request)
    id_token = token.get('id_token')
    user_info = decode_jwt(id_token)  # Decode JWT to extract user info
    if not user_info:
        raise HTTPException(status_code=400, detail="Failed to fetch user info from Apple")

    # Extract email from user info
    email = user_info.get('email')
    banned_user = await banned_collection.find_one({"email": email})
    if banned_user:
        raise HTTPException(
            status_code=403,
            detail="This email has been banned from the platform.")
    if not email:
        raise HTTPException(status_code=400, detail="Email is missing from Apple user info")

    # Extract username from email
    username_part = email.split('@')[0]
    username = username_part.capitalize()  # Capitalize the first letter of the username

    # Apple doesn't provide profile pictures
    profile_picture = None
    # Handle the user creation or login logic
    user = await handle_oauth_user(email, username, profile_picture, response)
    return {"message": "Login successful", "user": user}

@app.get('/auth/discord')
async def login_discord(request: Request):
    return await oauth.discord.authorize_redirect(request, DISCORD_REDIRECT_URI)

@app.get('/auth/discord/callback')
async def discord_callback(request: Request):
    token = await oauth.discord.authorize_access_token(request)
    user_info = await oauth.discord.get('users/@me', token=token)
    user_info = user_info.json()

    if not user_info:
        raise HTTPException(status_code=400, detail="Failed to fetch user info from Discord")

    email = user_info.get('email')
    banned_user = await banned_collection.find_one({"email": email})
    if banned_user:
        raise HTTPException(
            status_code=403,
            detail="This email has been banned from the platform.")
    username = user_info.get('username')
    profile_picture = f"https://cdn.discordapp.com/avatars/{user_info['id']}/{user_info['avatar']}.png" if user_info.get('avatar') else None

    user = await handle_oauth_user(email, username, profile_picture)
    return {"message": "Login successful", "user": user}

# Helper function to handle OAuth user info
async def handle_oauth_user(email, username, profile_picture, response: Response):
    if profile_picture is None:
        profile_picture = generate_profile_picture(username)
    user = await user_collection.find_one({"email": email})
    if not user:
        # Generate a unique handle
        base_handle = username.lower()
        while True:
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
            generated_handle = f"{base_handle}{random_suffix}"
            existing_handle = await user_collection.find_one({"handle": generated_handle})
            if not existing_handle:
                break

        # Create a new user if not exists
        new_user = {
            "username": username,
            "handle": generated_handle,  # Assign the generated handle
            "bio": "Hey! This is my bio",
            "pronouns": None,
            "badges": [],
            "email": email,
            "profile_picture": profile_picture,
            "is_verified": True,  # OAuth sign-ins are considered verified
            "streak": 0,  # Initialize streak
            "lumens": 1,  # Initialize lumens
            "socials": [],
            "roles": [],
            "followers": {
            "count": 0,  # Initialize with 0 followers
            "users": []  # Empty list of follower usernames
            },
            "following": {
                "count": 0,  # Initialize with 0 following
                "users": []  # Empty list of following usernames
            },
            "last_streak_update": None,
            "posts_read_count": 0,
            "joined_on": datetime.utcnow()
        }
        result = await user_collection.insert_one(new_user)
        user_id = str(result.inserted_id)
    else:
        # Existing user
        user_id = str(user["_id"])

    # Generate tokens
    access_token = create_access_token({"user_id": user_id}, expires_delta=timedelta(hours=2))
    refresh_token = create_access_token({"user_id": user_id}, expires_delta=timedelta(days=7))
    
    # Set tokens in cookies
    response.set_cookie(key="token", value=access_token, httponly=True, secure=True)
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=True)

    return {"success": True}

@app.get("/auth/verify/{verification_code}")
async def verify_email(verification_code: str):
    user = await verify_verification_code(verification_code, user_collection)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")

    await user_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"is_verified": True}, "$unset": {"verification_code": ""}}
    )

    return {"message": "Email verified successfully"}

@app.post("/user/edithandle", dependencies=[Depends(validate_access_token)])
async def edit_handle(handle_data: HandleSchema, access_payload: dict = Depends(validate_access_token)):
    user_id = access_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")
    
    new_handle = handle_data.handle.lower()  # Convert handle to lowercase
    
    if profanity.contains_profanity(new_handle):
        raise HTTPException(status_code=400, detail="Inappropriate words is not allowed in handle")

    # Check if the handle is already taken
    existing_user = await user_collection.find_one({"handle": new_handle})
    if existing_user:
        raise HTTPException(status_code=400, detail="Handle is already taken. Please choose a different one.")

    # Update the user's handle in the database
    result = await user_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"handle": new_handle}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"success": True, "message": "Handle updated successfully"}

@app.post("/user/editbio", dependencies=[Depends(validate_access_token)])
async def edit_handle(bio_data: BioSchema, access_payload: dict = Depends(validate_access_token)):
    user_id = access_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")
    
    if profanity.contains_profanity(bio_data.bio):
        raise HTTPException(status_code=400, detail="Inappropriate words is not allowed in bio")

    # Update the user's handle in the database
    result = await user_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"bio": bio_data.bio}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"success": True, "message": "Bio updated successfully"}

@app.post("/user/editpronouns", dependencies=[Depends(validate_access_token)])
async def edit_pronouns(
    pronouns_data: PronounsSchema, access_payload: dict = Depends(validate_access_token)
):
    # Extract the user_id from the access token payload
    user_id = access_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")

    # Fetch the user from the database
    user = await user_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update the pronouns in the user's profile
    await user_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"pronouns": pronouns_data.pronouns}}
    )

    return {
        "success": True,
        "message": f"Pronouns updated successfully for user '{user.get('username', 'Unknown')}'",
        "pronouns": pronouns_data.pronouns
    }

@app.post("/user/socials/add", dependencies=[Depends(validate_access_token)])
async def add_social_links(social_data: SocialLinksSchema, access_payload: dict = Depends(validate_access_token)):
    # Extract the user_id from the access token payload
    user_id = access_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")
    
    # Fetch the user from the database
    user = await user_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify each link in the input is a valid URL
    for link in social_data.socials:
        if not re.match(r'^(https?://)?([\w.-]+)+(:\d+)?(/[\w\.-]*)*$', str(link)):
            raise HTTPException(status_code=400, detail=f"Invalid URL: {link}")

    # Add the socials to the user's profile
    await user_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$addToSet": {"socials": {"$each": social_data.socials}}}  # Add each unique URL
    )

    return {
        "success": True,
        "message": f"Social links added successfully for user '{user.get('username', 'Unknown')}'",
        "socials": social_data.socials
    }

@app.post("/user/socials/remove", dependencies=[Depends(validate_access_token)])
async def remove_social_links(social_data: SocialLinksSchema, access_payload: dict = Depends(validate_access_token)):
    # Extract the user_id from the access token payload
    user_id = access_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")
    
    # Fetch the user from the database
    user = await user_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify each link in the input is a valid URL
    for link in social_data.socials:
        if not re.match(r'^(https?://)?([\w.-]+)+(:\d+)?(/[\w\.-]*)*$', str(link)):
            raise HTTPException(status_code=400, detail=f"Invalid URL: {link}")

    # Check if the provided links exist in the user's socials list
    for link in social_data.socials:
        if link not in user.get("socials", []):
            raise HTTPException(status_code=400, detail=f"URL '{link}' does not exist in your socials list")

    # Remove the socials from the user's profile
    await user_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$pull": {"socials": {"$in": social_data.socials}}}  # Remove the specified URLs
    )

    return {
        "success": True,
        "message": f"Social links removed successfully for user '{user.get('username', 'Unknown')}'",
        "socials": social_data.socials
    }

@app.post("/user/follow", dependencies=[Depends(validate_access_token)])
async def follow_user(
    input_data: FollowUnfollowSchema,
    access_payload: dict = Depends(validate_access_token),
):
    current_user_id = access_payload.get("user_id")
    if not current_user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")

    # Get the current user's profile
    current_user = await user_collection.find_one({"_id": ObjectId(current_user_id)})
    if not current_user:
        raise HTTPException(status_code=404, detail="Current user not found")

    # Get the target user's profile
    target_user = await user_collection.find_one({"_id": ObjectId(input_data.user_id)})
    if not target_user:
        raise HTTPException(status_code=404, detail="User to follow not found")

    # Check if already following
    if current_user["username"] in target_user["followers"]["users"]:
        raise HTTPException(status_code=400, detail="You are already following this user")

    # Update the target user's followers
    await user_collection.update_one(
        {"_id": ObjectId(input_data.user_id)},
        {
            "$addToSet": {"followers.users": current_user["username"]},
            "$inc": {"followers.count": 1},
        },
    )

    # Update the current user's following
    await user_collection.update_one(
        {"_id": ObjectId(current_user_id)},
        {
            "$addToSet": {"following.users": target_user["username"]},
            "$inc": {"following.count": 1},
        },
    )
    return {"message": f"You are now following {target_user['username']}"}


@app.post("/user/unfollow", dependencies=[Depends(validate_access_token)])
async def unfollow_user(
    input_data: FollowUnfollowSchema,
    access_payload: dict = Depends(validate_access_token),
):
    current_user_id = access_payload.get("user_id")
    if not current_user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")

    # Get the current user's profile
    current_user = await user_collection.find_one({"_id": ObjectId(current_user_id)})
    if not current_user:
        raise HTTPException(status_code=404, detail="Current user not found")

    # Get the target user's profile
    target_user = await user_collection.find_one({"_id": ObjectId(input_data.user_id)})
    if not target_user:
        raise HTTPException(status_code=404, detail="User to unfollow not found")

    # Check if not following
    if current_user["username"] not in target_user["followers"]["users"]:
        raise HTTPException(status_code=400, detail="You are not following this user")

    # Update the target user's followers
    await user_collection.update_one(
        {"_id": ObjectId(input_data.user_id)},
        {
            "$pull": {"followers.users": current_user["username"]},
            "$inc": {"followers.count": -1 if target_user["followers"]["count"] > 0 else 0},
        },
    )

    # Update the current user's following
    await user_collection.update_one(
        {"_id": ObjectId(current_user_id)},
        {
            "$pull": {"following.users": target_user["username"]},
            "$inc": {"following.count": -1 if current_user["following"]["count"] > 0 else 0},
        },
    )

    return {"message": f"You have unfollowed {target_user['username']}"}

@app.post("/user/get", dependencies=[Depends(validate_access_token)])
async def get_user_info(
    input_data: FollowUnfollowSchema,
    access_payload: dict = Depends(validate_access_token),
):
    requesting_user_id = access_payload.get("user_id")
    if not requesting_user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")

    # Fetch the requested user's profile
    user = await user_collection.find_one({"_id": ObjectId(input_data.user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prepare the response with required fields
    user_info = {
        "user_id": str(user["_id"]),
        "username": user["username"],
        "handle": user["handle"],
        "pronouns": user["pronouns"],
        "badges": user["badges"],
        "bio": user["bio"],
        "email": user["email"],
        "profile_picture": user["profile_picture"],
        "socials": user["socials"],
        "interests": user.get("interests", []),
        "is_verified": user["is_verified"],
        "roles": user.get("roles", []),
        "streak": user.get("streak", 0),
        "lumens": user.get("lumens", 1),
        "communities": user.get("communities", []),
        "followers": {
            "count": user["followers"]["count"],
            "users": user["followers"]["users"],
        },
        "following": {
            "count": user["following"]["count"],
            "users": user["following"]["users"],
        },
        "joined_on": user["joined_on"]
    }

    return {"success": True, "data": user_info}


@app.post("/login")
async def login(user: UserLogin, response: Response):
    """
    Logs in the user and returns a secure token for further requests.
    Creates two tokens: one with 7-day expiration stored in cookies (refresh_token),
    and one with 2-hour expiration returned in the response (access_token).
    """
    # Fetch user data from the database
    user_data = await user_collection.find_one({
        "$or": [{"email": user.email_or_username}, {"username": user.email_or_username}]
    })

    if not user_data or not verify_password(user.password, user_data["password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    if not user_data["is_verified"]:
        raise HTTPException(status_code=400, detail="Please verify your email before logging in")

    # Create the two tokens
    user_id = str(user_data["_id"])
    
    # Token with 7-day expiration (refresh token)
    refresh_token_expiration = timedelta(days=7)
    refresh_token = create_access_token({"user_id": user_id}, expires_delta=refresh_token_expiration)
    
    # Token with 2-hour expiration (access token)
    access_token_expiration = timedelta(hours=2)
    access_token = create_access_token({"user_id": user_id}, expires_delta=access_token_expiration)

    # Save the refresh token to the cookies
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=True)
    response.set_cookie(key="token", value=access_token, httponly=True, secure=True)
    return {"success": True}

@app.post("/resend-verification")
@limiter.limit("1/5min")
async def resend_verification(request: Request, data: ResendVerificationRequest, background_tasks: BackgroundTasks):
    """
    Resends the verification email to the user if not already verified.
    
    Args:
    - data: The body containing the email address of the user requesting a new verification link.
    
    Returns:
    - Success message if the email is resent.
    - Error if the user is already verified or does not exist.
    """
    email = data.email
    
    # Check if the user exists in the database with the given email
    user = await user_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if the user is already verified
    if user.get("is_verified"):
        raise HTTPException(status_code=400, detail="Your email is already verified.")
    
    # Generate a new verification code and update the user document
    verification_data = create_verification_code()
    await user_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"verification_code": verification_data}}
    )

    # Send the verification email
    background_tasks.add_task(send_verification_email, email, verification_data["code"])

    return {"message": "Verification email resent. Please check your inbox."}

@app.post("/genauthtoken")
async def gen_token(request: Request, response: Response):
    """
    Validates the refresh token and checks if the access token is expired. 
    If the access token is expired, generates a new one using the refresh token.
    """
    # Extract the refresh token from the cookies
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(status_code=400, detail="Refresh token missing")

    # Decode the refresh token to validate it
    payload = decode_jwt(refresh_token)

    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Check the expiration time of the refresh token
    exp_time = payload.get("exp")
    if datetime.utcfromtimestamp(exp_time) < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Refresh token expired")

    # access_token = request.cookies.get("token")

    # if not access_token:
    #     raise HTTPException(status_code=400, detail="Access token missing")

    # access_payload = decode_jwt(access_token)

    # if access_payload is None:
    #     raise HTTPException(status_code=401, detail="Invalid access token")

    # access_exp_time = access_payload.get("exp")
    # if datetime.utcfromtimestamp(access_exp_time) < datetime.utcnow():
    #     # If the access token is expired, create a new one
    #     new_access_token = create_access_token({"user_id": user_id}, expires_delta=timedelta(hours=2))
    #     return {"message": "Access token expired, new access token generated", "access_token": new_access_token}
    # else:
    #     # If the access token is still valid
    #     return {"message": "Your access token is already valid"}
    new_access_token = create_access_token({"user_id": user_id}, expires_delta=timedelta(hours=2))
    response.set_cookie(key="token", value=new_access_token, httponly=True, secure=True)
    return {"access_token": new_access_token}

@app.get("/images/{image_id}")
async def get_image(image_id: str):
    """
    Endpoint to serve images from MongoDB by their ObjectId.
    """
    image = await images_collection.find_one({"_id": ObjectId(image_id)})
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    # Convert binary data back into an image
    image_data = image["data"]
    pil_img = Image.open(io.BytesIO(image_data))

    # Serve the image as a streaming response
    img_io = io.BytesIO()
    pil_img.save(img_io, format="JPEG")
    img_io.seek(0)

    return StreamingResponse(img_io, media_type="image/jpeg")

@app.post("/interests/add", dependencies=[Depends(validate_access_token)])
async def add_interest(interests_data: Interests, access_payload: dict = Depends(validate_access_token)):
    """
    Adds new interests to the user's interest list.
    If the interest list does not exist, creates the list and adds the new interests.
    """
    user_id = access_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")

    user = await user_collection.find_one({"_id": ObjectId(user_id)})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if "interests" not in user or not isinstance(user["interests"], list):
        # If the field doesn't exist, initialize it with the provided interests
        await user_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"interests": interests_data.interests}}
        )
    else:
        # Filter out interests that already exist to avoid duplicates
        new_interests = [interest for interest in interests_data.interests if interest not in user["interests"]]
        if not new_interests:
            raise HTTPException(status_code=400, detail="All interests already exist")
        
        await user_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$addToSet": {"interests": {"$each": new_interests}}}
        )
    return {"success": True}


@app.post("/interests/remove", dependencies=[Depends(validate_access_token)])
async def delete_interest(interests_data: Interests, access_payload: dict = Depends(validate_access_token)):
    """
    Deletes specific interests from the user's interest list.
    If the list does not exist, throws an error.
    """
    user_id = access_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")

    user = await user_collection.find_one({"_id": ObjectId(user_id)})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if "interests" not in user or not isinstance(user["interests"], list):
        raise HTTPException(status_code=400, detail="No interests to delete")

    # Filter interests that are not in the user's list
    non_existent_interests = [interest for interest in interests_data.interests if interest not in user["interests"]]
    if non_existent_interests:
        raise HTTPException(
            status_code=404,
            detail=f"Some interests not found in the list: {non_existent_interests}"
        )

    await user_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$pull": {"interests": {"$in": interests_data.interests}}}
    )
    return {"success": True}


@app.post("/interests/get")
async def get_interests():
    return {"success": True, "all_interests": all_subcategories}


# Post creation endpoint
@app.post("/post/create", dependencies=[Depends(validate_access_token)])
async def create_post(post: PostCreateSchema, access_payload: dict = Depends(validate_access_token)):
    user_id = access_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")

    # Validate heading character limit
    if len(post.heading) > 250:
        raise HTTPException(status_code=400, detail="Heading cannot exceed 250 characters")

    # Validate description character limit
    if len(post.description) > 1000:
        raise HTTPException(status_code=400, detail="Description cannot exceed 1000 characters")

    # Process the image
    if isinstance(post.image, UploadFile):
        image_url = await process_uploaded_image_file(post.image)
    elif isinstance(post.image, str):  # If it's a URL
        url_regex = re.compile(r"^(https?|ftp)://[^\s/$.?#].[^\s]*$", re.IGNORECASE)
        if not url_regex.match(post.image):
            raise HTTPException(status_code=400, detail="Invalid URL format for image")
        image_url = post.image
    else:
        raise HTTPException(status_code=400, detail="Invalid image format")

    # Profanity check
    censored_heading = profanity.censor(post.heading)
    censored_description = profanity.censor(post.description)

    def count_censored_words(original_text, censored_text):
        original_words = original_text.split()
        censored_words = censored_text.split()
        return sum(1 for o, c in zip(original_words, censored_words) if o != c)

    censored_word_count = count_censored_words(post.heading, censored_heading)
    censored_word_count += count_censored_words(post.description, censored_description)

    if censored_word_count > 6:
        raise HTTPException(status_code=400, detail="The post contains too many inappropriate words (more than 6) and cannot be published.")

    # Check for duplicate posts
    duplicate_post = await posts_collection.find_one({
        "user_id": user_id,
        "heading": censored_heading,
        "description": censored_description
    })
    if duplicate_post:
        raise HTTPException(status_code=400, detail="You cannot create a post with identical content more than once.")

    # Generate the TLDR
    tldr_data = process_post(censored_heading, censored_description)
    tldr = tldr_data.get('tldr')
    tags = determine_tags(censored_heading, tldr, all_subcategories)

    # Prepare the post document
    post_document = {
        "post_id": str(uuid4()),  # Unique post ID
        "user_id": user_id,
        "heading": censored_heading,
        "tldr": tldr,
        "description": censored_description,
        "tags": tags,
        "image": image_url,
        "likes": {"count": 0, "users": []},
        "dislikes": {"count": 0, "users": []},
        "views": 0,
        "comments": [],
        "created_on": datetime.now(timezone.utc)
    }

    # Add community_id if the post is a community post
    if post.community_id:
        # Check if the user is a member of the community
        community_member = await community_collection.find_one({
            "community_id": post.community_id,
            "user_id": user_id
        })
        if not community_member:
            raise HTTPException(status_code=403, detail="You are not a member of this community and cannot create a post")

        # Add the community_id field
        post_document["community_id"] = post.community_id

    # Insert the post into the posts collection
    await posts_collection.insert_one(post_document)

    return {
        "success": True,
        "message": "Post created successfully" + (f" in community '{post.community_id}'" if post.community_id else ""),
        "post_id": post_document["post_id"]
    }

@app.post("/post/edit", dependencies=[Depends(validate_access_token)])
async def edit_post(updates: PostEditSchema, access_payload: dict = Depends(validate_access_token)):
    user_id = access_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")

    # Fetch the post based on post_id
    post = await posts_collection.find_one({"post_id": updates.post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Check if the user is the owner of the post
    if post["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="You are not authorized to edit this post")

    # If the post belongs to a community, check if the user is a member of the community
    if post.get("community_id"):
        community_member = await community_collection.find_one({
            "community_id": post["community_id"],
            "user_id": user_id
        })
        if not community_member:
            raise HTTPException(status_code=403, detail="You are not a member of this community and cannot edit this post")

    # Prepare the update data
    update_data = updates.dict(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="No new data to update")

    # Validate heading character limit if updated
    if "heading" in update_data and len(update_data["heading"]) > 250:
        raise HTTPException(status_code=400, detail="Heading cannot exceed 250 characters")

    # Validate description character limit if updated
    if "description" in update_data and len(update_data["description"]) > 1000:
        raise HTTPException(status_code=400, detail="Description cannot exceed 1000 characters")

    # Check if the provided data is different from the current data
    changes_made = False
    for key in ["heading", "description", "image"]:
        if key in update_data and update_data[key] != post.get(key):
            changes_made = True

    if not changes_made:
        raise HTTPException(status_code=400, detail="No changes detected in the provided data")

    # Validate for spam
    if "heading" in update_data and classify(update_data["heading"]):
        raise HTTPException(status_code=400, detail="The post heading is flagged as spam")
    if "description" in update_data and classify(update_data["description"]):
        raise HTTPException(status_code=400, detail="The post description is flagged as spam")

    def count_censored_words(original_text, censored_text):
        original_words = original_text.split()
        censored_words = censored_text.split()
        return sum(1 for o, c in zip(original_words, censored_words) if o != c)

    # Profanity filter and censorship count
    censored_word_count = 0
    if "heading" in update_data:
        censored_heading = profanity.censor(update_data["heading"])
        censored_word_count += count_censored_words(update_data["heading"], censored_heading)
        update_data["heading"] = censored_heading

    if "description" in update_data:
        censored_description = profanity.censor(update_data["description"])
        censored_word_count += count_censored_words(update_data["description"], censored_description)
        update_data["description"] = censored_description

    # Check if the total censored word count exceeds the limit
    if censored_word_count > 6:
        raise HTTPException(status_code=400, detail="The post contains too many inappropriate words (more than 6) and cannot be updated.")

    # If heading or description is updated, regenerate the TLDR
    if "heading" in update_data or "description" in update_data:
        tldr_data = determine_tags(update_data.get("heading", post["heading"]), 
                                 update_data.get("description", post["description"]), all_subcategories)
        update_data["tldr"] = tldr_data["tldr"]

    # Process the image if updated
    if "image" in update_data:
        if isinstance(update_data["image"], UploadFile):
            image_url = await process_uploaded_image_file(update_data["image"])
            update_data["image"] = image_url

    # Ensure the post remains in the same community if it's a community post
    if "community_id" in update_data:
        if update_data["community_id"] != post.get("community_id"):
            raise HTTPException(
                status_code=400,
                detail="You cannot change the community_id of an existing community post"
            )
    elif "community_id" not in update_data and "community_id" in post:
        update_data["community_id"] = post["community_id"]  # Retain the existing community_id if applicable

    # Update the post in the posts_collection
    await posts_collection.update_one({"post_id": updates.post_id}, {"$set": update_data})

    return {"success": True, "message": "Post updated successfully"}

@app.post("/post/get", dependencies=[Depends(validate_access_token)])
async def get_post_details(post_search: PostGetSchema, access_payload: dict = Depends(validate_access_token)):
    user_id = access_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")

    # If community_id is provided, check if the user is a member of the community
    if post_search.community_id:
        # Check if the user is a member of the community by looking in the community_collection
        community_member = await community_collection.find_one({
            "community_id": post_search.community_id,
            "user_id": user_id
        })
        if not community_member:
            raise HTTPException(status_code=403, detail="You are not a member of this community")

    # Fetch the post from posts_collection, optionally filtering by community_id
    query = {"post_id": post_search.post_id}
    if post_search.community_id:
        query["community_id"] = post_search.community_id

    post = await posts_collection.find_one(query)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Update the post's view count if the viewer is not the author
    post_author_id = post.get("user_id")
    if post_author_id != user_id:
        await posts_collection.update_one(
            {"post_id": post_search.post_id},
            {"$inc": {"views": 1}}
        )

    # Fetch streak-related variables from the user's profile
    user_data = await user_collection.find_one({"_id": ObjectId(user_id)})
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    streak = user_data.get("streak", 0)
    lumens = user_data.get("lumens", 1)
    last_streak_update = user_data.get("last_streak_update", None)
    posts_read_count = user_data.get("posts_read_count", 0)

    current_time = datetime.utcnow()

    # Handle streak logic: Increment streak once per day
    if last_streak_update:
        time_diff = current_time - last_streak_update
        if time_diff.total_seconds() > 86400:  # More than 24 hours
            streak = 0
            posts_read_count = 0  # Reset posts_read_count when streak is reset

    # Use read_posts_collection to track recently read posts
    read_posts = await read_posts_collection.find_one({"user_id": user_id})

    # Initialize the posts object if it doesn't exist
    if not read_posts:
        read_posts = {"user_id": user_id, "posts": {}}

    # Check if the post was already read
    if post_search.post_id not in read_posts["posts"]:
        # If it's the first post of the day (read_posts["posts"] is empty), increment the streak
        if len(read_posts["posts"]) == 0:
            streak += 1  # Increment streak once when the first post of the day is read

        # Increment posts_read_count only if the post hasn't been read today
        posts_read_count += 1

        # Add the post_id to the user's read posts as a key
        await read_posts_collection.update_one(
            {"user_id": user_id},
            {"$set": {f"posts.{post_search.post_id}": True}},  # Store post_id as a key with a value of True
            upsert=True  # Create a new record if it doesn't exist
        )

    # Earn lumens point for every 25 posts read
    if posts_read_count % 25 == 0:
        lumens += 1

    # Update user data in the database
    await user_collection.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$set": {
                "streak": streak,
                "lumens": lumens,
                "last_streak_update": current_time,
                "posts_read_count": posts_read_count
            }
        }
    )

    # Resolve user information for the post
    post_user_name = post.get("user_name", None)
    post_user_pfp = post.get("user_pfp", None)

    if post_user_name and post_user_pfp:
        # If user_name and user_pfp exist in the post (system-generated post)
        user = post_user_name
        pfp = post_user_pfp
    else:
        # Check for user_id in the post (user-generated post)
        post_user_id = post.get("user_id", None)
        if post_user_id:
            try:
                user_info = await user_collection.find_one(
                    {"_id": ObjectId(post_user_id)}, {"username": 1, "profile_picture.url": 1}
                )
                if user_info:
                    user = user_info.get("username", "Unknown")
                    pfp = user_info.get("profile_picture", {}).get("url", None)
                else:
                    user = "Unknown"
                    pfp = None
            except Exception:
                user = "Unknown"
                pfp = None
        else:
            user = "Unknown"
            pfp = None

    # Return the post details along with updated streak and lumens
    post_details = {
        "post_id": post["post_id"],
        "community_id": post.get("community_id", None),
        "user": user,
        "pfp": pfp,
        "heading": post["heading"],
        "image": post["image"],
        "tldr": post["tldr"],
        "description": post.get("description", None),
        "post_link": post.get("post_link", None),
        "tags": post["tags"],
        "created_on": post["created_on"],
        "likes": post["likes"],
        "views": post["views"],
        "dislikes": post["dislikes"],
        "comments": post["comments"]
    }

    return {"success": True, "post_details": post_details}

@app.post("/post/delete", dependencies=[Depends(validate_access_token)])
async def delete_post(data: PostDeleteSchema, access_payload: dict = Depends(validate_access_token)):
    user_id = access_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")
    
    # Check if community_id is provided
    if data.community_id:
        # Find the specified community
        community = await communities_collection.find_one({"community_id": data.community_id})
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check if the user is a member of the community
        community_member = await community_collection.find_one({
            "community_id": data.community_id,
            "user_id": user_id
        })
        if not community_member:
            raise HTTPException(status_code=403, detail="You are not a member of this community and cannot delete this post")
        
        # Check if the post exists in posts_collection with the given community_id
        post = await posts_collection.find_one({"post_id": data.post_id, "community_id": data.community_id})
        if not post:
            raise HTTPException(status_code=404, detail="Post not found in the specified community")

        # Check if the user is the owner of the post
        if post["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="You are not authorized to delete this post")
    else:
        # Default to deleting the post from the posts_collection if no community_id is provided
        post = await posts_collection.find_one({"post_id": data.post_id})
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        # Check if the user is the owner of the post
        if post["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="You are not authorized to delete this post")

    # Delete the post from the posts_collection
    await posts_collection.delete_one({"post_id": data.post_id})

    return {"success": True, "message": "Post deleted successfully"}

@app.post("/post/like", dependencies=[Depends(validate_access_token)])
async def like_post(post_data: PostGetSchema, access_payload: dict = Depends(validate_access_token)):
    user_id = access_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")
    
    # Check if community_id is provided
    if post_data.community_id:
        # Find the community
        community = await communities_collection.find_one({"community_id": post_data.community_id})
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check if the user is a member of the community
        community_member = await community_collection.find_one({
            "community_id": post_data.community_id,
            "user_id": user_id
        })
        if not community_member:
            raise HTTPException(status_code=403, detail="You are not a member of this community and cannot like this post")
        
        # Find the post in posts_collection
        post = await posts_collection.find_one({"post_id": post_data.post_id, "community_id": post_data.community_id})
        if not post:
            raise HTTPException(status_code=404, detail="Post not found in the specified community")

        # Check if the user has already liked the post
        user_liked = user_id in post["likes"]["users"]
        user_disliked = user_id in post["dislikes"]["users"]

        if user_liked:
            # Remove the user's like
            await posts_collection.update_one(
                {"post_id": post_data.post_id, "community_id": post_data.community_id},
                {
                    "$pull": {"likes.users": user_id},
                    "$inc": {"likes.count": -1}
                }
            )
            return {"success": True, "message": "Like removed"}
        else:
            # Add the user's like and ensure their dislike is removed if present
            update_query = {
                "$addToSet": {"likes.users": user_id},
                "$inc": {"likes.count": 1}
            }
            if user_disliked:
                update_query["$pull"] = {"dislikes.users": user_id}
                update_query["$inc"]["dislikes.count"] = -1
            
            await posts_collection.update_one(
                {"post_id": post_data.post_id, "community_id": post_data.community_id},
                update_query
            )
            return {"success": True, "message": "Post liked"}
    else:
        # Fallback to the global posts_collection if no community_id is provided
        post = await posts_collection.find_one({"post_id": post_data.post_id})
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Check if the user has already liked the post
        user_liked = user_id in post["likes"]["users"]
        user_disliked = user_id in post["dislikes"]["users"]

        if user_liked:
            # Remove the user's like
            await posts_collection.update_one(
                {"post_id": post_data.post_id},
                {
                    "$pull": {"likes.users": user_id},
                    "$inc": {"likes.count": -1}
                }
            )
            return {"success": True, "message": "Like removed"}
        else:
            # Add the user's like and ensure their dislike is removed if present
            update_query = {
                "$addToSet": {"likes.users": user_id},
                "$inc": {"likes.count": 1}
            }
            if user_disliked:
                update_query["$pull"] = {"dislikes.users": user_id}
                update_query["$inc"]["dislikes.count"] = -1
            
            await posts_collection.update_one({"post_id": post_data.post_id}, update_query)
            return {"success": True, "message": "Post liked"}

@app.post("/post/dislike", dependencies=[Depends(validate_access_token)])
async def dislike_post(post_data: PostGetSchema, access_payload: dict = Depends(validate_access_token)):
    user_id = access_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")
    
    # Check if community_id is provided
    if post_data.community_id:
        # Find the community
        community = await communities_collection.find_one({"community_id": post_data.community_id})
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check if the user is a member of the community
        community_member = await community_collection.find_one({
            "community_id": post_data.community_id,
            "user_id": user_id
        })
        if not community_member:
            raise HTTPException(status_code=403, detail="You are not a member of this community and cannot dislike this post")
        
        # Find the post in posts_collection
        post = await posts_collection.find_one({"post_id": post_data.post_id, "community_id": post_data.community_id})
        if not post:
            raise HTTPException(status_code=404, detail="Post not found in the specified community")

        # Check if the user has already disliked the post
        user_liked = user_id in post["likes"]["users"]
        user_disliked = user_id in post["dislikes"]["users"]

        if user_disliked:
            # Remove the user's dislike
            await posts_collection.update_one(
                {"post_id": post_data.post_id, "community_id": post_data.community_id},
                {
                    "$pull": {"dislikes.users": user_id},
                    "$inc": {"dislikes.count": -1}
                }
            )
            return {"success": True, "message": "Dislike removed"}
        else:
            # Add the user's dislike and ensure their like is removed if present
            update_query = {
                "$addToSet": {"dislikes.users": user_id},
                "$inc": {"dislikes.count": 1}
            }
            if user_liked:
                update_query["$pull"] = {"likes.users": user_id}
                update_query["$inc"]["likes.count"] = -1
            
            await posts_collection.update_one(
                {"post_id": post_data.post_id, "community_id": post_data.community_id},
                update_query
            )
            return {"success": True, "message": "Post disliked"}
    else:
        # Fallback to the global posts_collection if no community_id is provided
        post = await posts_collection.find_one({"post_id": post_data.post_id})
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Check if the user has already disliked the post
        user_liked = user_id in post["likes"]["users"]
        user_disliked = user_id in post["dislikes"]["users"]

        if user_disliked:
            # Remove the user's dislike
            await posts_collection.update_one(
                {"post_id": post_data.post_id},
                {
                    "$pull": {"dislikes.users": user_id},
                    "$inc": {"dislikes.count": -1}
                }
            )
            return {"success": True, "message": "Dislike removed"}
        else:
            # Add the user's dislike and ensure their like is removed if present
            update_query = {
                "$addToSet": {"dislikes.users": user_id},
                "$inc": {"dislikes.count": 1}
            }
            if user_liked:
                update_query["$pull"] = {"likes.users": user_id}
                update_query["$inc"]["likes.count"] = -1
            
            await posts_collection.update_one({"post_id": post_data.post_id}, update_query)
            return {"success": True, "message": "Post disliked"}

@app.post("/post/comment/create", dependencies=[Depends(validate_access_token)])
async def create_comment(
    comment_data: CommentCreateSchema, access_payload: dict = Depends(validate_access_token)
):
    user_id = access_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")

    # Check if community_id is provided
    if comment_data.community_id:
        # Find the community
        community = await communities_collection.find_one({"community_id": comment_data.community_id})
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check if the user is a member of the community
        community_member = await community_collection.find_one({
            "community_id": comment_data.community_id,
            "user_id": user_id
        })
        if not community_member:
            raise HTTPException(status_code=403, detail="You are not a member of this community and cannot comment")

    # Find the post in the global posts collection
    post = await posts_collection.find_one({"post_id": comment_data.post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Validate the comment text
    if classify(comment_data.text):
        raise HTTPException(status_code=400, detail="The comment is flagged as spam")

    censored_text = profanity.censor(comment_data.text)

    def count_censored_words(original_text, censored_text):
        original_words = original_text.split()
        censored_words = censored_text.split()
        return sum(1 for o, c in zip(original_words, censored_words) if o != c)

    censored_word_count = count_censored_words(comment_data.text, censored_text)
    if censored_word_count > 6:
        raise HTTPException(status_code=400, detail="The comment contains too many inappropriate words (more than 6) and cannot be created.")

    # Fetch user details for comment metadata
    try:
        user_data = await user_collection.find_one({"_id": ObjectId(user_id)}, {"username": 1, "profile_picture.url": 1})
        username = user_data.get("username", "Unknown")
        pfp = user_data.get("profile_picture", {}).get("url", None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user details: {str(e)}")

    # Ensure no duplicate comment by the same user
    existing_comment = next(
        (comment for comment in post.get("comments", []) if comment["user_id"] == user_id and comment["text"] == comment_data.text),
        None
    )
    if existing_comment:
        raise HTTPException(status_code=400, detail="You cannot post the same comment text multiple times.")

    comment_id = str(uuid4())
    new_comment = {
        "comment_id": comment_id,
        "user_id": user_id,
        "username": username,
        "pfp": pfp,
        "text": censored_text,
        "likes": {"count": 0, "users": []},
        "dislikes": {"count": 0, "users": []},
        "created_on": datetime.utcnow()
    }

    # Add comment to the global post
    await posts_collection.update_one(
        {"post_id": comment_data.post_id},
        {"$push": {"comments": new_comment}}
    )

    return {"success": True, "message": "Comment added successfully", "comment_id": comment_id}

@app.post("/post/comment/edit", dependencies=[Depends(validate_access_token)])
async def edit_comment(data: CommentEditSchema, access_payload: dict = Depends(validate_access_token)):
    user_id = access_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")

    # Check if community_id is provided
    if data.community_id:
        # Find the community
        community = await communities_collection.find_one({"community_id": data.community_id})
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check if the user is a member of the community
        community_member = await community_collection.find_one({
            "community_id": data.community_id,
            "user_id": user_id
        })
        if not community_member:
            raise HTTPException(status_code=403, detail="You are not a member of this community and cannot edit this comment")

    # Find the post in the global posts collection
    post = await posts_collection.find_one({"comments.comment_id": data.comment_id})
    if not post:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Validate the comment text
    if classify(data.text):
        raise HTTPException(status_code=400, detail="The comment is flagged as spam")

    censored_text = profanity.censor(data.text)

    def count_censored_words(original_text, censored_text):
        original_words = original_text.split()
        censored_words = censored_text.split()
        return sum(1 for o, c in zip(original_words, censored_words) if o != c)

    censored_word_count = count_censored_words(data.text, censored_text)
    if censored_word_count > 6:
        raise HTTPException(status_code=400, detail="The comment contains too many inappropriate words (more than 6) and cannot be edited.")

    # Find the comment
    comment = next((c for c in post["comments"] if c["comment_id"] == data.comment_id), None)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="You are not authorized to edit this comment")

    if comment["text"] == data.text:
        raise HTTPException(status_code=400, detail="No changes detected in the comment text")

    # Update comment in the global post
    await posts_collection.update_one(
        {"comments.comment_id": data.comment_id},
        {"$set": {"comments.$.text": censored_text}}
    )

    return {"success": True, "message": "Comment edited successfully"}

@app.post("/post/comment/delete", dependencies=[Depends(validate_access_token)])
async def delete_comment(data: CommentDeleteSchema, access_payload: dict = Depends(validate_access_token)):
    user_id = access_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")

    # Check if community_id is provided
    if data.community_id:
        # Find the community
        community = await communities_collection.find_one({"community_id": data.community_id})
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check if the user is a member of the community
        community_member = await community_collection.find_one({
            "community_id": data.community_id,
            "user_id": user_id
        })
        if not community_member:
            raise HTTPException(status_code=403, detail="You are not a member of this community and cannot delete this comment")

    # Find the post containing the comment in the global posts collection
    post = await posts_collection.find_one({"comments.comment_id": data.comment_id})
    if not post:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Find the specific comment
    comment = next((c for c in post["comments"] if c["comment_id"] == data.comment_id), None)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="You are not authorized to delete this comment")

    # Delete the comment from the global post
    await posts_collection.update_one(
        {"post_id": post["post_id"]},
        {"$pull": {"comments": {"comment_id": data.comment_id}}}
    )

    return {"success": True, "message": "Comment deleted successfully"}

@app.post("/comment/like", dependencies=[Depends(validate_access_token)])
async def like_comment(data: CommentLikeSchema, access_payload: dict = Depends(validate_access_token)):
    user_id = access_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")

    # Check if community_id is provided
    if data.community_id:
        # Find the community
        community = await communities_collection.find_one({"community_id": data.community_id})
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check if the user is a member of the community
        community_member = await community_collection.find_one({
            "community_id": data.community_id,
            "user_id": user_id
        })
        if not community_member:
            raise HTTPException(status_code=403, detail="You are not a member of this community and cannot like this comment")

    # Find the post containing the comment in the global posts collection
    post = await posts_collection.find_one({"comments.comment_id": data.comment_id})
    if not post:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Find the specific comment inside the post
    comment = next((c for c in post["comments"] if c["comment_id"] == data.comment_id), None)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Check if the user already liked or disliked the comment
    user_already_liked = user_id in comment["likes"]["users"]
    user_already_disliked = user_id in comment["dislikes"]["users"]

    update_query = {}

    if user_already_liked:
        # Remove the like
        update_query = {
            "$pull": {"comments.$[comment].likes.users": user_id},
            "$inc": {"comments.$[comment].likes.count": -1}
        }
    else:
        # Add the like
        update_query["$addToSet"] = {"comments.$[comment].likes.users": user_id}
        update_query["$inc"] = {"comments.$[comment].likes.count": 1}

        if user_already_disliked:
            # Remove the dislike
            update_query["$pull"] = {"comments.$[comment].dislikes.users": user_id}
            update_query["$inc"] = {"comments.$[comment].dislikes.count": -1}

    # Update the comment in the post
    await posts_collection.update_one(
        {"comments.comment_id": data.comment_id},
        update_query,
        array_filters=[{"comment.comment_id": data.comment_id}]
    )

    return {"success": True, "message": "Comment liked/unliked successfully"}

@app.post("/comment/dislike", dependencies=[Depends(validate_access_token)])
async def dislike_comment(data: CommentDislikeSchema, access_payload: dict = Depends(validate_access_token)):
    user_id = access_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")

    # Check if community_id is provided
    if data.community_id:
        # Find the community
        community = await communities_collection.find_one({"community_id": data.community_id})
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check if the user is a member of the community
        community_member = await community_collection.find_one({
            "community_id": data.community_id,
            "user_id": user_id
        })
        if not community_member:
            raise HTTPException(status_code=403, detail="You are not a member of this community and cannot dislike this comment")

    # Find the post containing the comment in the global posts collection
    post = await posts_collection.find_one({"comments.comment_id": data.comment_id})
    if not post:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Find the specific comment inside the post
    comment = next((c for c in post["comments"] if c["comment_id"] == data.comment_id), None)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Check if the user already liked or disliked the comment
    user_already_liked = user_id in comment["likes"]["users"]
    user_already_disliked = user_id in comment["dislikes"]["users"]

    update_query = {}

    if user_already_disliked:
        # Remove the dislike
        update_query = {
            "$pull": {"comments.$[comment].dislikes.users": user_id},
            "$inc": {"comments.$[comment].dislikes.count": -1}
        }
    else:
        # Add the dislike
        update_query["$addToSet"] = {"comments.$[comment].dislikes.users": user_id}
        update_query["$inc"] = {"comments.$[comment].dislikes.count": 1}

        if user_already_liked:
            # Remove the like
            update_query["$pull"] = {"comments.$[comment].likes.users": user_id}
            update_query["$inc"] = {"comments.$[comment].likes.count": -1}

    # Update the comment in the post
    await posts_collection.update_one(
        {"comments.comment_id": data.comment_id},
        update_query,
        array_filters=[{"comment.comment_id": data.comment_id}]
    )

    return {"success": True, "message": "Comment disliked/undisliked successfully"}


@app.post("/post/report", dependencies=[Depends(validate_access_token)])
async def report_post(report_data: PostReportSchema, access_payload: dict = Depends(validate_access_token)):
    user_id = access_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")

    # Fetch the username from the user_collection using the user_id
    user = await user_collection.find_one({"_id": ObjectId(user_id)}, {"username": 1})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    username = user.get("username", "Unknown")

    # Validate the reason and description limits
    if len(report_data.reason) > 250:
        raise HTTPException(status_code=400, detail="Reason cannot exceed 250 characters")
    if len(report_data.description) > 1000:
        raise HTTPException(status_code=400, detail="Description cannot exceed 1000 characters")

    # Fetch the post in the global posts collection
    post = await posts_collection.find_one({"post_id": report_data.post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Check if the user has already reported the post with the same details
    existing_report = await reports_collection.find_one({
        "user_id": user_id,
        "post_id": report_data.post_id,
        "reason": report_data.reason,
        "description": report_data.description
    })
    if existing_report:
        raise HTTPException(status_code=400, detail="You are reporting the same post too many times.")

    # Generate a unique report ID
    report_id = str(uuid4())

    # Create the report document
    report_document = {
        "report_id": report_id,
        "user_id": user_id,
        "username": username,
        "post_id": report_data.post_id,
        "reason": report_data.reason,
        "description": report_data.description,
        "created_on": datetime.utcnow()
    }

    # Save the report in the reports_collection
    await reports_collection.insert_one(report_document)

    return {"success": True, "message": "Report submitted successfully", "report_id": report_id}

@app.post("/comment/report", dependencies=[Depends(validate_access_token)])
async def report_comment(report_data: CommentReportSchema, access_payload: dict = Depends(validate_access_token)):
    user_id = access_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")

    # Fetch the username from the user_collection using the user_id
    user = await user_collection.find_one({"_id": ObjectId(user_id)}, {"username": 1})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    username = user.get("username", "Unknown")

    # Validate the reason and description limits
    if len(report_data.reason) > 250:
        raise HTTPException(status_code=400, detail="Reason cannot exceed 250 characters")
    if len(report_data.description) > 1000:
        raise HTTPException(status_code=400, detail="Description cannot exceed 1000 characters")

    # Fetch the post containing the comment in the global posts collection
    post = await posts_collection.find_one({"comments.comment_id": report_data.comment_id})
    if not post:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Find the specific comment in the post
    comment = next((c for c in post["comments"] if c["comment_id"] == report_data.comment_id), None)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Extract the comment text and author ID
    comment_text = comment.get("text", "No text available")
    comment_author = comment.get("user_id", "Unknown")

    # Check if the user has already reported the comment with the same details
    existing_report = await reports_collection.find_one({
        "user_id": user_id,
        "comment_id": report_data.comment_id,
        "reason": report_data.reason,
        "description": report_data.description
    })
    if existing_report:
        raise HTTPException(status_code=400, detail="You are reporting the same comment too many times.")

    # Generate a unique report ID
    report_id = str(uuid4())

    # Create the report document
    report_document = {
        "report_id": report_id,
        "user_id": user_id,
        "username": username,
        "comment_id": report_data.comment_id,
        "reason": report_data.reason,
        "description": report_data.description,
        "comment_text": comment_text,
        "comment_author": comment_author,
        "created_on": datetime.utcnow()
    }

    # Save the report in the reports_collection
    await reports_collection.insert_one(report_document)

    return {"success": True, "message": "Report submitted successfully", "report_id": report_id}

@app.post("/streak/restore", dependencies=[Depends(validate_access_token)])
async def restore_streak(access_payload: dict = Depends(validate_access_token)):
    user_id = access_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")

    # Fetch user data from the database
    from bson import ObjectId  # Ensure bson is imported
    user_data = await user_collection.find_one({"_id": ObjectId(user_id)})
    
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    # Extract streak, lumens, and last_streak_update details
    streak = user_data.get("streak", 0)
    lumens = user_data.get("lumens", 1)
    last_streak_update = user_data.get("last_streak_update", None)

    current_time = datetime.utcnow()

    if not last_streak_update:
        raise HTTPException(status_code=400, detail="No previous streak data available to restore.")

    # Calculate time difference since the last streak update
    time_diff = current_time - last_streak_update
    if time_diff.total_seconds() <= 86400:
        raise HTTPException(status_code=400, detail="Your streak has not been reset; no restoration needed.")

    if lumens <= 0:
        raise HTTPException(status_code=400, detail="Not enough lumens points to restore streak.")

    # Restore the streak and deduct 1 lumens point
    await user_collection.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$set": {
                "last_streak_update": current_time  # Reset the streak update time
            },
            "$inc": {
                "lumens": -1  # Deduct 1 lumens point
            }
        }
    )
    return {
        "success": True,
        "message": f"Your streak has been restored to {streak}. 1 lumens point has been deducted.",
        "streak": streak,
        "remaining_lumens": lumens - 1
    }

@app.post("/community/create", dependencies=[Depends(validate_access_token)])
async def create_community(
    community_data: CommunityCreateSchema, 
    access_payload: dict = Depends(validate_access_token)
):
    user_id = access_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")

    # Check if the user already has a community with the same name and description
    existing_community = await communities_collection.find_one({
        "user_id": user_id,
        "community_name": community_data.community_name,
        "community_description": community_data.community_description
    })
    
    if existing_community:
        raise HTTPException(
            status_code=400,
            detail="You have already created a community with the same name and description."
        )

    # Generate a unique community ID
    community_id = str(uuid4())
    # Current timestamp for community creation
    created_on = datetime.utcnow()

    # Determine the value of "posts_is_admin_only" based on the user's input
    posts_is_admin_only = community_data.posts_is_admin_only if community_data.posts_is_admin_only else False
    
    def generate_invitation_id(length=7):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    invitation_id = generate_invitation_id()

    # Construct the community document
    new_community = {
        "community_id": community_id,
        "user_id": user_id,  # The creator's user ID
        "invitation_id": invitation_id,  # Unique invitation ID for joining the community
        "community_name": community_data.community_name,
        "community_description": community_data.community_description,
        "posts_is_admin_only": posts_is_admin_only,  # Use the provided value or default to False
        "member_count": 1,
        "community_tags": community_data.community_tags,
        "algorithm_tags": [],  # No algorithm tags at the beginning
        "banned_users": [], # No banned users at the beginning
        "created_roles": [
            {
                "role_name": "Admin",
                "role_colour": "#fcbe33",
            },
            {
                "role_name": "Moderator",
                "role_colour": "#24cc3c",
            },
        ],  # Admin can define roles later
        "created_on": created_on,
    }

    # Save the community to the `communities_collection`
    await communities_collection.insert_one(new_community)

    # Create a separate entry in the community_collection to track user role and join information
    community_for_user = {
        "user_id": user_id,
        "community_id": community_id,
        "community_name": community_data.community_name,
        "roles": ["Admin"],  # Assign Admin role
        "joined_on": created_on,
    }

    # Save the community membership in the new `community_collection`
    await community_collection.insert_one(community_for_user)

    return {
        "success": True,
        "message": "Community created successfully!",
        "community_id": community_id,
        "community_name": community_data.community_name,
        "posts_is_admin_only": posts_is_admin_only,
    }

@app.post("/community/get", dependencies=[Depends(validate_access_token)])
async def get_community(community_data: CommunityActionSchema, access_payload: dict = Depends(validate_access_token)):
    user_id = access_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")

    # Fetch the community-member record for the requesting user
    community_member = await community_collection.find_one({
        "community_id": community_data.community_id,
        "user_id": user_id
    })
    if not community_member:
        raise HTTPException(status_code=403, detail="You are not a member of this community")

    # Fetch the community details from communities_collection
    community = await communities_collection.find_one({"community_id": community_data.community_id})
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    # Check if the user is the owner, admin, or moderator of the community
    is_owner = community["user_id"] == user_id
    user_roles = community_member.get("roles", [])
    is_admin_or_moderator = "Admin" in user_roles or "Moderator" in user_roles

    if not (is_owner or is_admin_or_moderator):
        raise HTTPException(
            status_code=403,
            detail="You must be the Admin, Owner, or Moderator of the community to access this information"
        )

    # Return the community details
    return {
        "success": True,
        "community_details": {
            "community_id": community["community_id"],
            "user_id": community["user_id"],
            "invitation_id": community["invitation_id"],  # Unique invitation link
            "community_name": community["community_name"],
            "community_description": community["community_description"],
            "posts_is_admin_only": community["posts_is_admin_only"],
            "member_count": community["member_count"],
            "community_tags": community["community_tags"],
            "algorithm_tags": community["algorithm_tags"],
            "banned_users": community.get("banned_users", []),
            "created_roles": community.get("created_roles", []),
            "created_on": community["created_on"],
        },
    }


@app.post("/community/posts", dependencies=[Depends(validate_access_token)])
async def fetch_community_posts(input: CommunityPostsSchema, access_payload: dict = Depends(validate_access_token)):
    """
    Fetches a specified number of posts from the posts collection based on a community_id,
    sorted by latest to oldest.
    """
    user_id = access_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")

    # Validate the community_id exists
    community = await communities_collection.find_one({"community_id": input.community_id})
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    # Fetch posts from the posts collection where the community_id matches
    posts_cursor = posts_collection.find({"community_id": input.community_id}).sort("created_on", -1)

    # Limit the number of posts fetched
    posts = await posts_cursor.to_list(length=input.posts)

    # If no posts are found, return an appropriate message
    if not posts:
        raise HTTPException(status_code=404, detail="No posts available in this community")

    # Convert `created_on` field to ISO format for consistency
    for post in posts:
        post["created_on"] = post["created_on"].isoformat()

    return {
        "success": True,
        "community_id": input.community_id,
        "posts": posts
    }

@app.post("/community/role/create", dependencies=[Depends(validate_access_token)])
async def create_role(role_data: RoleCreateSchema, access_payload: dict = Depends(validate_access_token)):
    user_id = access_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")
    
    # Fetch the community by ID from the new community_collection
    community = await community_collection.find_one({"community_id": role_data.community_id})
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    # Check the user's roles in the community
    user_roles = next(
        (
            member["roles"]
            for member in community.get("members", [])
            if member["user_id"] == user_id
        ),
        None,
    )

    if not user_roles or not any(role in user_roles for role in ["Admin", "Moderator"]):
        raise HTTPException(status_code=403, detail="You are not authorized to create roles in this community")

    # Check if the role already exists in the community
    if any(role["role_name"].lower() == role_data.role_name.lower() for role in community["created_roles"]):
        raise HTTPException(status_code=400, detail="Role with this name already exists in the community")

    # Check for profanity in the role name
    if profanity.contains_profanity(role_data.role_name):
        raise HTTPException(status_code=400, detail="Role name contains inappropriate or foul language")

    # Add the new role to the community
    new_role = {
        "role_name": role_data.role_name,
        "role_colour": role_data.role_colour,
    }

    await community_collection.update_one(
        {"community_id": role_data.community_id},
        {"$push": {"created_roles": new_role}}
    )

    return {
        "success": True,
        "message": f"Role '{role_data.role_name}' created successfully in community '{community['community_name']}'",
        "role": new_role,
    }


@app.post("/community/role/edit", dependencies=[Depends(validate_access_token)])
async def edit_role(role_data: RoleEditSchema, access_payload: dict = Depends(validate_access_token)):
    user_id = access_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")
    
    # Fetch the community by ID from the new community_collection
    community = await community_collection.find_one({"community_id": role_data.community_id})
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    # Check the user's roles in the community
    user_roles = next(
        (
            member["roles"]
            for member in community.get("members", [])
            if member["user_id"] == user_id
        ),
        None,
    )

    if not user_roles or not any(role in user_roles for role in ["Admin", "Moderator"]):
        raise HTTPException(status_code=403, detail="You are not authorized to edit roles in this community")

    # Ensure the role exists in the created_roles list
    role_to_edit = next(
        (
            role
            for role in community["created_roles"]
            if role["role_name"].lower() == role_data.role_name.lower()
        ),
        None,
    )
    if not role_to_edit:
        raise HTTPException(status_code=404, detail="Role not found in the community's created_roles list")

    # Check if the user is attempting to edit a system-created role
    is_system_role = role_to_edit["role_name"].lower() in ["admin", "moderator"]

    # Disallow changing the name of system-created roles
    if is_system_role and role_data.new_role_name:
        raise HTTPException(
            status_code=403,
            detail="Cannot change the name of system-created roles like 'Admin' or 'Moderator'"
        )

    # Check if the new role name or color matches the existing values
    if role_data.new_role_name:
        if role_to_edit["role_name"].lower() == role_data.new_role_name.lower():
            raise HTTPException(
                status_code=400,
                detail="The new role name is the same as the current role name. No changes were made."
            )

    # Only validate color change if a new role color is provided
    if role_data.role_colour and not role_data.new_role_name and role_to_edit["role_colour"] == role_data.role_colour:
        raise HTTPException(
            status_code=400,
            detail="The new role color is the same as the current role color. No changes were made."
        )

    # Check for profanity in the new role name
    if role_data.new_role_name and profanity.contains_profanity(role_data.new_role_name):
        raise HTTPException(status_code=400, detail="Role name contains inappropriate or foul language")

    # Prepare the updated role
    updated_role = {
        "role_name": role_to_edit["role_name"] if is_system_role else (role_data.new_role_name or role_to_edit["role_name"]),
        "role_colour": role_data.role_colour or role_to_edit["role_colour"],  # Update color only if provided
    }

    # Update the role in the community's created_roles list
    await community_collection.update_one(
        {"community_id": role_data.community_id, "created_roles.role_name": role_to_edit["role_name"]},
        {"$set": {"created_roles.$": updated_role}}
    )

    return {
        "success": True,
        "message": f"Role '{role_to_edit['role_name']}' updated successfully in community '{community['community_name']}'",
        "updated_role": updated_role,
    }


@app.post("/community/role/add", dependencies=[Depends(validate_access_token)])
async def add_role_to_user(role_data: RoleAssignSchema, access_payload: dict = Depends(validate_access_token)):
    # Extract the current user's ID
    current_user_id = access_payload.get("user_id")
    if not current_user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")

    # Fetch the community by ID
    community = await communities_collection.find_one({"community_id": role_data.community_id})
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    # Check if the current user is authorized to add roles
    community_member = await community_collection.find_one({
        "community_id": role_data.community_id,
        "user_id": current_user_id
    })
    
    if not community_member:
        raise HTTPException(status_code=403, detail="You are not a member of this community and cannot add roles")

    # Check if the user has the necessary roles (Admin or Moderator) in the community
    if not any(role in community_member["roles"] for role in ["Admin", "Moderator"]):
        raise HTTPException(status_code=403, detail="You are not authorized to add roles in this community")

    # Ensure the role to be assigned exists in the community's created_roles
    if not any(role["role_name"].lower() == role_data.role_name.lower() for role in community["created_roles"]):
        raise HTTPException(status_code=400, detail="Role does not exist in this community")

    # Check if the user to whom the role is being added exists in the community (using community_collection)
    community_member_to_add_role = await community_collection.find_one({
        "community_id": role_data.community_id,
        "user_id": role_data.user_id
    })
    if not community_member_to_add_role:
        raise HTTPException(status_code=404, detail="Target user is not a member of this community")

    # Ensure the role is not already assigned to the user
    if role_data.role_name in community_member_to_add_role["roles"]:
        raise HTTPException(status_code=400, detail="User already has this role in the community")

    # Add the role to the user's roles in the community collection
    await community_collection.update_one(
        {"community_id": role_data.community_id, "user_id": role_data.user_id},
        {"$push": {"roles": role_data.role_name}}
    )

    return {
        "success": True,
        "message": f"Role '{role_data.role_name}' successfully added to user '{role_data.user_id}' in community '{community['community_name']}'"
    }

@app.post("/community/role/remove", dependencies=[Depends(validate_access_token)])
async def remove_role_from_user(role_data: RoleAssignSchema, access_payload: dict = Depends(validate_access_token)):
    # Extract the current user's ID
    current_user_id = access_payload.get("user_id")
    if not current_user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")

    # Fetch the community by ID
    community = await communities_collection.find_one({"community_id": role_data.community_id})
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    # Check if the current user is authorized to remove roles
    community_member = await community_collection.find_one({
        "community_id": role_data.community_id,
        "user_id": current_user_id
    })
    
    if not community_member:
        raise HTTPException(status_code=403, detail="You are not a member of this community and cannot remove roles")

    # Check if the user has the necessary roles (Admin or Moderator) in the community
    if not any(role in community_member["roles"] for role in ["Admin", "Moderator"]):
        raise HTTPException(status_code=403, detail="You are not authorized to remove roles in this community")

    # Fetch the target user's entry in the community
    community_member_to_remove_role = await community_collection.find_one({
        "community_id": role_data.community_id,
        "user_id": role_data.user_id
    })
    if not community_member_to_remove_role:
        raise HTTPException(status_code=404, detail="Target user is not a member of this community")

    # Ensure that the role exists in the user's roles
    if role_data.role_name not in community_member_to_remove_role["roles"]:
        raise HTTPException(status_code=400, detail="User does not have this role in the community")

    # Check permissions: Moderators cannot remove the Admin's role
    if role_data.role_name == "Admin" and "Moderator" in community_member["roles"]:
        raise HTTPException(status_code=403, detail="Moderators cannot remove the Admin's role")

    # Remove the role from the user's roles in the community collection
    await community_collection.update_one(
        {"community_id": role_data.community_id, "user_id": role_data.user_id},
        {"$pull": {"roles": role_data.role_name}}
    )

    return {
        "success": True,
        "message": f"Role '{role_data.role_name}' successfully removed from user '{role_data.user_id}' in community '{community['community_name']}'"
    }

@app.post("/community/role/delete", dependencies=[Depends(validate_access_token)])
async def delete_role(role_data: RoleDeleteSchema, access_payload: dict = Depends(validate_access_token)):
    user_id = access_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")

    # Fetch the community by ID
    community = await communities_collection.find_one({"community_id": role_data.community_id})
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    # Check if the user has sufficient permissions (Admin or Moderator)
    community_member = await communities_collection.find_one({
        "community_id": role_data.community_id,
        "members.user_id": user_id
    })
    if not community_member:
        raise HTTPException(status_code=403, detail="You are not a member of this community")

    if not any(role in community_member["roles"] for role in ["Admin", "Moderator"]):
        raise HTTPException(status_code=403, detail="You are not authorized to delete roles in this community")

    # Ensure the role exists in the created_roles list
    if not any(role["role_name"].lower() == role_data.role_name.lower() for role in community["created_roles"]):
        raise HTTPException(status_code=404, detail="Role not found in the community's created_roles list")
    
    if role_data.role_name.lower() in ["admin", "moderator"]:
        raise HTTPException(status_code=403, detail="System-created roles like 'Admin' and 'Moderator' cannot be deleted")

    # Delete the role from the created_roles list
    await communities_collection.update_one(
        {"community_id": role_data.community_id},
        {"$pull": {"created_roles": {"role_name": role_data.role_name}}}
    )
    return {
        "success": True,
        "message": f"Role '{role_data.role_name}' deleted successfully from community '{community['community_name']}'"
    }

@app.post("/community/delete", dependencies=[Depends(validate_access_token)])
async def delete_community(community_data: CommunityDeleteSchema, access_payload: dict = Depends(validate_access_token)):
    user_id = access_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")

    # Fetch the community by ID
    community = await communities_collection.find_one({"community_id": community_data.community_id})
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    # Check if the user is the owner or has the Admin role in the community
    if community["user_id"] != user_id:
        # Check if the user is a member of the community with Admin privileges
        community_member = await communities_collection.find_one({
            "community_id": community_data.community_id,
            "members.user_id": user_id
        })
        if not community_member:
            raise HTTPException(status_code=403, detail="You are not a member of this community")

        if "Admin" not in community_member["roles"]:
            raise HTTPException(status_code=403, detail="You are not authorized to delete this community")

    # Delete the community from `communities_collection`
    await communities_collection.delete_one({"community_id": community_data.community_id})

    # Remove all members of the community from the `members` array in `community_collection`
    await communities_collection.update_many(
        {"community_id": community_data.community_id},
        {"$pull": {"members": {"community_id": community_data.community_id}}}
    )

    return {
        "success": True,
        "message": f"Community '{community['community_name']}' has been deleted successfully.",
        "community_id": community_data.community_id,
    }

@app.post("/community/join", dependencies=[Depends(validate_access_token)])
async def join_community(community_data: CommunityActionSchema, access_payload: dict = Depends(validate_access_token)):
    user_id = access_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")

    # Fetch the community by either community_id or invitation_id
    community = None
    if community_data.community_id:
        community = await communities_collection.find_one({"community_id": community_data.community_id})
    elif community_data.invitation_id:
        community = await communities_collection.find_one({"invitation_id": community_data.invitation_id})
    
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    # Fetch the user's profile
    user_profile = await user_collection.find_one({"_id": ObjectId(user_id)})
    if not user_profile:
        raise HTTPException(status_code=404, detail="User profile not found")

    # Check if the user is already a member of the community in the community_collection
    existing_member = await community_collection.find_one({
        "community_id": community["community_id"],
        "user_id": user_id
    })
    if existing_member:
        raise HTTPException(status_code=400, detail="User is already a member of this community")
    
    if user_id in community.get("banned_users", []):
        raise HTTPException(status_code=403, detail="You are banned from this community and cannot join.")

    # Add the community to the community_collection for the user
    created_on = datetime.utcnow()
    community_for_user_profile = {
        "user_id": user_id,
        "community_id": community["community_id"],
        "community_name": community["community_name"],
        "roles": [],  # New members start with no roles
        "joined_on": created_on,
    }

    # Save the community membership in the `community_collection`
    await community_collection.insert_one(community_for_user_profile)

    # Increment the community's member count
    await communities_collection.update_one(
        {"community_id": community["community_id"]},
        {"$inc": {"member_count": 1}}
    )

    return {
        "success": True,
        "message": f"Successfully joined the community '{community['community_name']}'",
    }

@app.post("/community/leave", dependencies=[Depends(validate_access_token)])
async def leave_community(community_data: CommunityActionSchema, access_payload: dict = Depends(validate_access_token)):
    user_id = access_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")

    # Fetch the community by either community_id or invitation_id
    community = None
    if community_data.community_id:
        community = await communities_collection.find_one({"community_id": community_data.community_id})
    elif community_data.invitation_id:
        community = await communities_collection.find_one({"invitation_id": community_data.invitation_id})
    
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    # Fetch the user's profile
    user_profile = await user_collection.find_one({"_id": ObjectId(user_id)})
    if not user_profile:
        raise HTTPException(status_code=404, detail="User profile not found")

    # Check if the user is a member of the community in the community_collection
    user_in_community = await community_collection.find_one({
        "community_id": community["community_id"],
        "user_id": user_id
    })
    if not user_in_community:
        raise HTTPException(status_code=400, detail="User is not a member of this community")

    # Check if the user is the Admin of the community
    if community["user_id"] == user_id:
        raise HTTPException(
            status_code=403,
            detail="Admin of the community cannot leave the community they created"
        )
    
    # Remove the user from the community in the `community_collection`
    await community_collection.delete_one({
        "community_id": community["community_id"],
        "user_id": user_id
    })

    # Ensure member count does not go below 1
    if community["member_count"] > 1:
        await communities_collection.update_one(
            {"community_id": community["community_id"]},
            {"$inc": {"member_count": -1}}
        )

    return {
        "success": True,
        "message": f"Successfully left the community '{community['community_name']}'",
    }

@app.post("/community/report", dependencies=[Depends(validate_access_token)])
async def report_community(report_data: CommunityReportSchema, access_payload: dict = Depends(validate_access_token)):
    user_id = access_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")

    # Fetch the username from the user_collection using the user_id
    user = await user_collection.find_one({"_id": ObjectId(user_id)}, {"username": 1})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    username = user.get("username", "Unknown")

    # Validate the reason and description limits
    if len(report_data.reason) > 250:
        raise HTTPException(status_code=400, detail="Reason cannot exceed 250 characters")
    if len(report_data.description) > 1000:
        raise HTTPException(status_code=400, detail="Description cannot exceed 1000 characters")

    # Check if the community exists
    community = await communities_collection.find_one({"community_id": report_data.community_id}, {"name": 1, "description": 1})
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    # Extract community name and description
    community_name = community.get("name", "Unknown")
    community_description = community.get("description", "No description available")

    # Check if the user has already reported the same community with the same details
    existing_report = await reports_collection.find_one({
        "user_id": user_id,
        "community_id": report_data.community_id,
        "reason": report_data.reason,
        "description": report_data.description
    })
    if existing_report:
        raise HTTPException(status_code=400, detail="You are reporting the same community too many times.")

    # Generate a unique report ID
    report_id = str(uuid4())

    # Create the report document
    report_document = {
        "report_id": report_id,
        "user_id": user_id,
        "username": username,
        "community_id": report_data.community_id,
        "community_name": community_name,
        "community_description": community_description,
        "reason": report_data.reason,
        "description": report_data.description,
        "created_on": datetime.utcnow()
    }

    # Save the report in the reports_collection
    await reports_collection.insert_one(report_document)

    return {"success": True, "message": "Report submitted successfully", "report_id": report_id}

@app.post("/community/ban", dependencies=[Depends(validate_access_token)])
async def ban_user(community_data: CommunityModerationSchema, access_payload: dict = Depends(validate_access_token)):
    user_id = access_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")

    # Fetch the community-member record of the user performing the action
    requesting_member = await community_collection.find_one({
        "community_id": community_data.community_id,
        "user_id": user_id
    })
    if not requesting_member:
        raise HTTPException(status_code=404, detail="You are not a member of this community")
    
    if not any(role in requesting_member["roles"] for role in ["Admin", "Moderator"]):
        raise HTTPException(status_code=403, detail="You don't have Moderator or Admin privileges")

    # Fetch the community-member record of the target user
    target_member = await community_collection.find_one({
        "community_id": community_data.community_id,
        "user_id": community_data.user_id
    })
    if not target_member:
        raise HTTPException(status_code=400, detail="User is not a member of this community")

    # Add the user to the banned list and remove them from the community
    await community_collection.update_one(
        {"community_id": community_data.community_id, "user_id": community_data.user_id},
        {"$set": {"banned": True}}
    )
    return {
        "success": True,
        "message": f"User has been banned from the community '{requesting_member['community_name']}'"
    }

@app.post("/community/unban", dependencies=[Depends(validate_access_token)])
async def unban_user(community_data: CommunityModerationSchema, access_payload: dict = Depends(validate_access_token)):
    user_id = access_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")

    # Fetch the community-member record of the user performing the action
    requesting_member = await community_collection.find_one({
        "community_id": community_data.community_id,
        "user_id": user_id
    })
    if not requesting_member:
        raise HTTPException(status_code=404, detail="You are not a member of this community")

    if not any(role in requesting_member["roles"] for role in ["Admin", "Moderator"]):
        raise HTTPException(status_code=403, detail="You don't have Moderator or Admin privileges")

    # Fetch the community-member record of the target user
    target_member = await community_collection.find_one({
        "community_id": community_data.community_id,
        "user_id": community_data.user_id
    })
    if not target_member or not target_member.get("banned"):
        raise HTTPException(status_code=400, detail="User is not banned from this community")

    # Remove the banned flag from the user
    await community_collection.update_one(
        {"community_id": community_data.community_id, "user_id": community_data.user_id},
        {"$set": {"banned": False}}
    )
    return {
        "success": True,
        "message": f"User has been unbanned from the community '{requesting_member['community_name']}'"
    }

@app.post("/community/kick", dependencies=[Depends(validate_access_token)])
async def kick_user(community_data: CommunityModerationSchema, access_payload: dict = Depends(validate_access_token)):
    user_id = access_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")

    # Fetch the community-member record of the user performing the action
    requesting_member = await community_collection.find_one({
        "community_id": community_data.community_id,
        "user_id": user_id
    })
    if not requesting_member:
        raise HTTPException(status_code=404, detail="You are not a member of this community")

    if not any(role in requesting_member["roles"] for role in ["Admin", "Moderator"]):
        raise HTTPException(status_code=403, detail="You don't have Moderator or Admin privileges")

    # Fetch the community-member record of the target user
    target_member = await community_collection.find_one({
        "community_id": community_data.community_id,
        "user_id": community_data.user_id
    })
    if not target_member:
        raise HTTPException(status_code=400, detail="User is not a member of this community")

    # Remove the user from the community by deleting their entry
    await community_collection.delete_one({
        "community_id": community_data.community_id,
        "user_id": community_data.user_id
    })
    return {
        "success": True,
        "message": f"User has been kicked from the community '{requesting_member['community_name']}'"
    }

@app.post("/team/report/get", dependencies=[Depends(validate_access_token)])
async def get_reports(access_payload: dict = Depends(validate_access_token)):
    # Get the user's handle based on their user_id
    user_id = access_payload.get("user_id")
    user = await user_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if the user's handle is authorized
    if user["handle"] not in TEAM_MEMBERS_HANDLES:
        raise HTTPException(status_code=403, detail="You are not authorized to access this endpoint.")

    # Fetch all reports from the reports_collection
    reports = await reports_collection.find({}).to_list(None)
    return {"success": True, "reports": reports}

@app.post("/team/report/clear", dependencies=[Depends(validate_access_token)])
async def clear_report(reportschema: ReportClearSchema, access_payload: dict = Depends(validate_access_token)):
    # Extract the report_id from the input schema
    if not reportschema.report_id:
        raise HTTPException(status_code=400, detail="Report ID is required.")

    # Get the user's handle based on their user_id
    user_id = access_payload.get("user_id")
    user = await user_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if the user's handle is authorized
    if user["handle"] not in TEAM_MEMBERS_HANDLES:
        raise HTTPException(status_code=403, detail="You are not authorized to access this endpoint.")

    # Attempt to delete the report from the database
    delete_result = await reports_collection.delete_one({"_id": ObjectId(reportschema.report_id)})
    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Report not found.")

    return {"success": True, "message": "Report has been cleared successfully."}

@app.post("/team/user/warn", dependencies=[Depends(validate_access_token)])
async def warn_user(user_input: FollowUnfollowSchema, user_id: str = Depends(validate_access_token)):
    """Warn a user for violating terms and conditions"""
    
    # Get the current user's handle
    user_handle = await user_collection.find_one({"_id": user_id}, {"handle": 1})
    if not user_handle:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_handle = user_handle['handle']
    
    # Check if the current user is a team member and authorized to warn
    if user_handle not in TEAM_MEMBERS_HANDLES:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    # Check if the team member is trying to warn another team member
    warned_user = await user_collection.find_one({"_id": user_input.user_id})
    if not warned_user:
        raise HTTPException(status_code=404, detail="User to warn not found")
    
    warned_user_handle = warned_user.get('handle')
    if warned_user_handle in TEAM_MEMBERS_HANDLES:
        raise HTTPException(status_code=403, detail="Cannot warn another team member")

    # Get the username and email of the user being warned
    email = warned_user.get("email")
    username = warned_user.get("username")
    
    # Send a warning email to the user
    await send_warn_email(email=email, username=username)
    
    return {"success": True, "message": f"User {username} has been successfully warned."}

@app.post("/team/user/ban", dependencies=[Depends(validate_access_token)])
async def ban_user(user_input: FollowUnfollowSchema, user_id: str = Depends(validate_access_token)):
    """Ban a user for violating terms and conditions"""
    
    # Get the current user's handle
    user_handle = await user_collection.find_one({"_id": user_id}, {"handle": 1})
    if not user_handle:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_handle = user_handle['handle']
    
    # Check if the current user is a team member and authorized to ban
    if user_handle not in TEAM_MEMBERS_HANDLES:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    # Get the user being banned's data
    banned_user = await user_collection.find_one({"_id": user_input.user_id})
    if not banned_user:
        raise HTTPException(status_code=404, detail="User to ban not found")
    
    banned_user_handle = banned_user.get('handle')
    
    # Check if the team member is trying to ban another team member
    if banned_user_handle in TEAM_MEMBERS_HANDLES:
        raise HTTPException(status_code=403, detail="Cannot ban another team member")

    # Get the username and email of the user being banned
    email = banned_user.get("email")
    username = banned_user.get("username")
    
    # Add the user to the banned collection
    banned_data = {
        "user_id": user_input.user_id,
        "email": email,
        "username": username,
        "reason": "Violation of terms and conditions"
    }
    await banned_collection.insert_one(banned_data)
    
    # Delete the banned user's account
    await user_collection.delete_one({"_id": user_input.user_id})
    
    # Send a ban email to the user
    await send_ban_email(email=email, username=username)
    
    return {"success": True, "message": f"User {username} has been successfully banned."}

@app.post("/team/role/add", dependencies=[Depends(validate_access_token)])
async def add_team_role(role_data: RoleGiveSchema, access_payload: dict = Depends(validate_access_token)):
    # Extract user_id from the access token payload
    user_id = access_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")

    # Fetch the user's profile to get the handle
    user_profile = await user_collection.find_one({"_id": ObjectId(user_id)})
    if not user_profile:
        raise HTTPException(status_code=404, detail="User profile not found")

    # Check if the user's handle is in TEAM_MEMBER_HANDLES
    user_handle = user_profile.get("handle")
    if user_handle not in TEAM_MEMBERS_HANDLES:
        raise HTTPException(status_code=403, detail="You are not authorized to use this endpoint")

    # Fetch the user to whom the role will be assigned (from role_data.user_id)
    target_user = await user_collection.find_one({"_id": ObjectId(role_data.user_id)})
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")

    # Check if the role already exists in the target user's roles list
    if any(role["role_name"].lower() == role_data.role_name.lower() for role in target_user.get("roles", [])):
        raise HTTPException(status_code=400, detail="Role with this name already exists for the user")

    # Check for profanity in the role name
    if profanity.contains_profanity(role_data.role_name):
        raise HTTPException(status_code=400, detail="Role name contains inappropriate or foul language")

    # Add the new role to the target user's roles list
    new_role = {
        "role_name": role_data.role_name,
        "role_colour": role_data.role_colour,
    }

    await user_collection.update_one(
        {"_id": ObjectId(role_data.user_id)},
        {"$push": {"roles": new_role}}
    )

    return {
        "success": True,
        "message": f"Role '{role_data.role_name}' added successfully to user '{target_user.get('username', 'Unknown')}'",
        "role": new_role,
    }

@app.post("/team/role/remove", dependencies=[Depends(validate_access_token)])
async def remove_team_role(role_data: RoleGiveSchema, access_payload: dict = Depends(validate_access_token)):
    # Extract user_id from the access token payload
    user_id = access_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid access token payload")

    # Fetch the user's profile to get the handle
    user_profile = await user_collection.find_one({"_id": ObjectId(user_id)})
    if not user_profile:
        raise HTTPException(status_code=404, detail="User profile not found")

    # Check if the user's handle is in TEAM_MEMBER_HANDLES
    user_handle = user_profile.get("handle")
    if user_handle not in TEAM_MEMBERS_HANDLES:
        raise HTTPException(status_code=403, detail="You are not authorized to use this endpoint")

    # Fetch the user from whom the role will be removed (from role_data.user_id)
    target_user = await user_collection.find_one({"_id": ObjectId(role_data.user_id)})
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")

    # Check if the role exists in the target user's roles list
    role_to_remove = next(
        (role for role in target_user.get("roles", []) if role["role_name"].lower() == role_data.role_name.lower()),
        None
    )
    if not role_to_remove:
        raise HTTPException(status_code=404, detail="Role not found for the user")

    # Remove the role from the target user's roles list
    await user_collection.update_one(
        {"_id": ObjectId(role_data.user_id)},
        {"$pull": {"roles": {"role_name": role_data.role_name}}}
    )

    return {
        "success": True,
        "message": f"Role '{role_data.role_name}' removed successfully from user '{target_user.get('username', 'Unknown')}'",
    }


@app.post("/algorithm/recommend/posts", dependencies=[Depends(validate_access_token)])
async def recommend_posts(data: AlgorithmRecommendPostsSchema, access_payload: dict = Depends(validate_access_token)):
    user_id = access_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=403, detail="Invalid access token payload")

    # Call the recommendation function for posts
    recommendations = await recommend_content(user_id=user_id, max_posts=data.posts)
    
    if "recommended_posts" not in recommendations:
        raise HTTPException(status_code=404, detail="No recommended posts found")

    return {"recommended_posts": recommendations["recommended_posts"]}

# Endpoint for recommending communities
@app.post("/algorithm/recommend/communities", dependencies=[Depends(validate_access_token)])
async def recommend_communities(data: AlgorithmRecommendCommunitySchema, access_payload: dict = Depends(validate_access_token)):
    user_id = access_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=403, detail="Invalid access token payload")

    # Call the recommendation function for communities
    recommendations = await recommend_content(user_id=user_id, max_communities=data.communities)
    
    if "recommended_communities" not in recommendations:
        raise HTTPException(status_code=404, detail="No recommended communities found")

    return {"recommended_communities": recommendations["recommended_communities"]}

# Endpoint for recommending users
@app.post("/algorithm/recommend/users", dependencies=[Depends(validate_access_token)])
async def recommend_users(data: AlgorithmRecommendUsersSchema, access_payload: dict = Depends(validate_access_token)):
    user_id = access_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=403, detail="Invalid access token payload")

    # Call the recommendation function for users
    recommendations = await recommend_content(user_id=user_id, max_users=data.users)
    
    if "recommended_users" not in recommendations:
        raise HTTPException(status_code=404, detail="No recommended users found")

    return {"recommended_users": recommendations["recommended_users"]}

@app.post("/spark/chat")
async def spark_chat(request: ChatRequestSchema, access_payload: str = Depends(validate_access_token)):
    # Validate access token
    try:
        shutil.rmtree("chroma_db")
    except Exception as e:
        print(e)
        pass
    user_id = access_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=403, detail="Invalid access token payload")
    # Check for profanity in the question
    if profanity.contains_profanity(request.question):
        raise HTTPException(status_code=400, detail="Profanity detected in the question.")
    # Proceed to get the answer from Spark
    try:
        if request.post_ids:
            answer = await sparkai.spark_answer(post_ids=request.post_ids, question=request.question)
        else:
            answer = await sparkai.spark_answer(question=request.question)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)
