import os
import feedparser
import re
import random
import datetime
from datetime import timedelta
from generators.gen_post_info import process_post  # Import process_heading
from handlers.create_system_posts import create_post_without_token  # Import create_post_without_token

# Persistent storage for the latest fetched post titles (log file)
POST_LOG_FILE = os.path.join("logs", "medium_posts.log")
MAX_RETRIES = 6  # Maximum number of retries for generating TLDR and tags
# Define the time limit for recent posts (2 weeks ago)
TWO_WEEKS_AGO = datetime.datetime.now() - timedelta(weeks=2)

# Users or pages to fetch from
MEDIUM_USERS = [
    "@veruscoin",
    "@blockchain",
    "dailyjs",
    "@javascripting",
    "@madewithjavascript",
    "@pythonclcoding",
    "@nodejs",
    "@loseheart110",
    "stackademic",
    "codex",
    "generative-ai",
    "@cryptorand",
    "@learnreact",
    "flutter-community",
    "stackanatomy"
]


def get_latest_post_titles():
    """Retrieve the last fetched post titles from the log file."""
    if os.path.exists(POST_LOG_FILE):
        with open(POST_LOG_FILE, "r") as file:
            return set(file.read().splitlines())
    return set()


def save_latest_post_titles(titles):
    """Save the latest fetched post titles to the log file."""
    os.makedirs(os.path.dirname(POST_LOG_FILE), exist_ok=True)
    # Ensure all titles are Unicode-safe
    safe_titles = [title.encode("ascii", errors="ignore").decode("ascii") for title in titles]
    with open(POST_LOG_FILE, "w", encoding="utf-8") as file:
        file.write("\n".join(safe_titles))


def clean_html(raw_html):
    """Remove HTML and XML tags from a string."""
    cleanr = re.compile('<.*?>')
    return re.sub(cleanr, '', raw_html)


def get_summary_text(summary):
    """Extract a clean summary from the feed entry summary."""
    clean_summary = clean_html(summary)
    sentences = clean_summary.split(". ")
    return ". ".join(sentences[:3]) + "." if sentences else clean_summary


def ensure_tldr_and_tags(heading, description):
    """Ensure that TLDR and tags are populated by retrying `process_heading`."""
    retries = 0
    tldr, tags = "", []
    while (not tldr or not tags) and retries < MAX_RETRIES:
        processed_data = process_post(heading, description)
        tldr = tldr or processed_data.get("tldr", "")
        tags = tags or processed_data.get("tags", [])
        retries += 1
    return tldr, tags


def generate_post_id():
    """Generate a random unique post ID."""
    return f"post_{random.randint(100000, 999999)}"


async def fetch_and_save_medium_posts(num_of_posts=5):
    """Fetch posts from Medium RSS feeds and save them."""
    latest_post_titles = get_latest_post_titles()
    new_titles = set()

    for user in MEDIUM_USERS:
        rss_url = f"https://medium.com/feed/{user}"
        feed = feedparser.parse(rss_url)

        if not feed.entries:
            print(f"No entries found for RSS URL: {rss_url}")
            continue

        for entry in feed.entries[:num_of_posts]:
            # Parse the published date
            published_date = None
            if hasattr(entry, 'published_parsed'):
                published_date = datetime.datetime(*entry.published_parsed[:6])

            # Skip the post if no date is available or it's older than 2 weeks
            if not published_date or published_date < TWO_WEEKS_AGO:
                print(f"Skipping old post: {entry.title} (Published on {published_date})")
                continue

            heading = clean_html(entry.title)
            post_link = entry.link
            description = get_summary_text(entry.summary)

            # Skip already fetched posts
            if heading in latest_post_titles:
                print(f"Skipping already fetched post: {heading}")
                continue

            # Extract the first image URL from the summary
            image_url = None
            image_match = re.search(r'<img[^>]+src="([^">]+)"', entry.summary)
            if image_match:
                image_url = image_match.group(1)

            # Generate TLDR and tags
            tldr, tags = ensure_tldr_and_tags(heading, description)
            print(tldr, tags)
            
            # Prepare the data for posting
            post_data = {
                "post_id": generate_post_id(),
                "user_name": "Medium",
                "user_pfp": "https://favicon.im/medium.com",
                "heading": heading,
                "image_url": image_url,
                "tldr": tldr,
                "description": description,
                "tags": tags
            }

            # Save the post using the create_post_without_token function
            response = await create_post_without_token(
                user_name=post_data["user_name"],
                user_pfp=post_data["user_pfp"],
                heading=post_data["heading"],
                tldr=post_data["tldr"],
                image=post_data["image_url"],
                tags=post_data["tags"],
                post_link=post_link,
            )

            print(f"Response from create_post_without_token: {response}")

            # Add the title to the new_titles set
            new_titles.add(heading)

    # Update the persistent storage with new titles
    save_latest_post_titles(latest_post_titles.union(new_titles))

    if not new_titles:
        print("No new posts were fetched.")