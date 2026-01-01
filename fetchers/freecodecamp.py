import os
import requests
from bs4 import BeautifulSoup
from generators.gen_post_info import process_heading  # Import process_heading
from handlers.create_system_posts import create_post_without_token  # Import create_post_without_token

# Persistent storage for the latest fetched post titles (log file)
POST_LOG_FILE = os.path.join("logs", "freecodecamp.log")
MAX_RETRIES = 6  # Maximum number of retries for generating TLDR and tags


def get_latest_post_titles():
    """Retrieve the last fetched post titles from the log file."""
    if os.path.exists(POST_LOG_FILE):
        with open(POST_LOG_FILE, "r") as file:
            return set(file.read().splitlines())
    return set()


def save_latest_post_titles(titles):
    """Save the latest fetched post titles to the log file."""
    os.makedirs(os.path.dirname(POST_LOG_FILE), exist_ok=True)  # Ensure resources folder exists
    with open(POST_LOG_FILE, "w") as file:
        file.write("\n".join(titles))


def ensure_tldr_and_tags(heading, current_tldr, current_tags):
    """
    Ensure that the TLDR and tags are populated by retrying `process_heading` if they are missing.
    :param heading: The post heading.
    :param current_tldr: Current TLDR value.
    :param current_tags: Current tags list.
    :return: A tuple of (tldr, tags).
    """
    retries = 0
    while (not current_tldr or not current_tags) and retries < MAX_RETRIES:
        processed_data = process_heading(heading)
        current_tldr = current_tldr or processed_data.get("tldr", "")
        current_tags = current_tags or processed_data.get("tags", [])
        retries += 1
    return current_tldr, current_tags


async def fetch_posts_from_freecodecamp(num_of_posts=5):
    """
    Fetches the latest posts from freeCodeCamp News and creates system posts.

    :param num_of_posts: Number of posts to fetch.
    :return: None
    """
    url = "https://www.freecodecamp.org/news/"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch {url}. HTTP Status: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    post_cards = soup.find_all("h2", class_="post-card-title")

    if not post_cards:
        print("No posts found on the page.")
        return

    latest_post_titles = get_latest_post_titles()
    new_titles = set()

    for post in post_cards:
        if len(new_titles) >= num_of_posts:
            break

        anchor = post.find("a")
        if not anchor:
            continue

        post_title = anchor.text.strip()
        post_url = "https://www.freecodecamp.org" + anchor["href"]

        # Skip if this post has already been fetched
        if post_title in latest_post_titles:
            print(f"Skipping already fetched post: {post_title}")
            continue

        # Fetch the post page for more details
        post_response = requests.get(post_url)
        if post_response.status_code != 200:
            print(f"Failed to fetch post URL {post_url}. Skipping...")
            continue

        post_soup = BeautifulSoup(post_response.text, "html.parser")
        post_heading = post_soup.find("h1", class_="post-full-title").text.strip()

        # Extract the image URL
        picture = post_soup.find("picture")
        image_url = None
        if picture:
            source = picture.find("source", media="(min-width: 701px)")
            if source and "srcset" in source.attrs:
                image_url = source["srcset"]

        # Generate TLDR and tags using process_heading
        processed_data = process_heading(post_heading)
        tldr = processed_data.get("tldr", "")
        tags = processed_data.get("tags", [])

        # Ensure TLDR and tags are populated
        tldr, tags = ensure_tldr_and_tags(post_heading, tldr, tags)

        # Call the create_post_without_token function to create the post in the database
        user_name = "FreeCodeCamp"
        user_pfp = "https://favicon.im/www.freecodecamp.org"

        response = await create_post_without_token(
            user_name=user_name,
            user_pfp=user_pfp,
            heading=post_heading,
            tldr=tldr,
            image=image_url,
            tags=tags,
            post_link=post_url,
        )

        print(f"Response from create_post_without_token: {response}")

        # Add the title to the new_titles set
        new_titles.add(post_title)

    # Update the persistent storage with new titles
    save_latest_post_titles(latest_post_titles.union(new_titles))

    if not new_titles:
        print("No new posts were fetched.")