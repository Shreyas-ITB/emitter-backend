import asyncio
from fetchers.freecodecamp import fetch_posts_from_freecodecamp
from fetchers.medium import fetch_and_save_medium_posts

# Example usage
async def main():
    # Fetch the latest 25 posts from freeCodeCamp News
    num_of_posts = 25
    print(f"Fetching the latest {num_of_posts} posts from freeCodeCamp News...")
    await fetch_posts_from_freecodecamp(num_of_posts=num_of_posts)
    # Fetch the latest 10 posts from Medium
    num_of_posts = 72
    print(f"Fetching the latest {num_of_posts} posts from Medium...")
    await fetch_and_save_medium_posts(num_of_posts=num_of_posts)

# Run the `main` coroutine
if __name__ == "__main__":
    asyncio.run(main())
