from datetime import datetime, timezone
from typing import List
from uuid import uuid4
import re
from handlers.config import posts_collection, images_collection
from better_profanity import profanity
from generators.spam_model import classify

profanity.load_censor_words()

def validate_tags(tags: List[str]):
    for tag in tags:
        if profanity.contains_profanity(tag):
            raise ValueError(f"Tag '{tag}' contains inappropriate language and is not allowed.")

async def create_post_without_token(user_name: str, user_pfp: str, heading: str, tldr: str, image: str, tags: List[str], post_link: str):
    """
    Creates a post in the database without user token validation and handles user_pfp in images_collection.

    Args:
        user_name (str): The name of the user creating the post.
        user_pfp (str): The profile picture URL of the user.
        heading (str): The heading/title of the post.
        tldr (str): The TLDR summary of the post.
        image (str): The image URL for the post.
        tags (List[str]): A list of tags for the post.
        post_link (str): The link to the full post.

    Returns:
        dict: A success message with details about the post creation or a message indicating duplication.

    Raises:
        ValueError: If validation fails for any of the fields.
    """

    # Validate heading character limit
    if len(heading) > 250:
        raise ValueError("Heading cannot exceed 250 characters")

    # Validate TLDR character limit
    if not tldr or len(tldr) > 600:
        raise ValueError("TLDR is required and cannot exceed 600 characters")

    # Validate tags
    if len(tags) < 5:
        raise ValueError("A minimum of 5 tags is required")

    # Validate post link
    url_regex = re.compile(r"^(https?|ftp)://[^\s/$.?#].[^\s]*$", re.IGNORECASE)
    if not url_regex.match(post_link):
        raise ValueError("Invalid URL format for the post link")
    
    censored_heading = profanity.censor(heading)
    censored_tags = [profanity.censor(tag) for tag in tags]

    def count_censored_words(original_text, censored_text):
        original_words = original_text.split()
        censored_words = censored_text.split()
        return sum(1 for o, c in zip(original_words, censored_words) if o != c)

    censored_word_count = count_censored_words(heading, censored_heading)
    censored_word_count += sum(
        count_censored_words(tag, censored_tag) for tag, censored_tag in zip(tags, censored_tags)
    )

    if classify(heading) or any(classify(tag) for tag in tags):
        raise ValueError("The post content is flagged as spam")

    if censored_word_count > 6:
        raise ValueError("The post contains too many inappropriate words (more than 6) and cannot be published.")

    # Validate image URL
    if not url_regex.match(image):
        raise ValueError("Invalid URL format for the image")

    # Validate user profile picture URL
    if not url_regex.match(user_pfp):
        raise ValueError("Invalid URL format for the user's profile picture")

    # Check if a post with the same heading and post link already exists
    existing_post = await posts_collection.find_one({"heading": heading, "post_link": post_link})
    if existing_post:
        return {"success": False, "message": "Post already exists in the database"}

    # Check if the user and their profile picture already exist in the images collection
    existing_user_pfp = await images_collection.find_one({"user_name": user_name, "user_pfp": user_pfp})
    if not existing_user_pfp:
        # If not found, insert the user profile picture
        await images_collection.insert_one({
            "user_name": user_name,
            "user_pfp": user_pfp
        })

    # Create post document
    post_document = {
        "post_id": str(uuid4()),  # Unique post ID
        "user_name": user_name,
        "user_pfp": user_pfp,
        "heading": heading,
        "tldr": tldr,
        "image": image,
        "tags": tags,
        "post_link": post_link,
        "created_on": datetime.now(timezone.utc),
        "likes": {"count": 0, "users": []},
        "dislikes": {"count": 0, "users": []},
        "views": 0,
        "comments": []
    }

    # Insert post into the database
    await posts_collection.insert_one(post_document)

    return {"success": True, "message": "Post created successfully", "post_id": post_document["post_id"]}