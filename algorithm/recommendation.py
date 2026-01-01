import random
from datetime import datetime
from pymongo import DESCENDING
from bson import ObjectId
from handlers.config import user_collection, posts_collection, communities_collection

async def recommend_content(
    user_id: str,
    max_posts: int = None,  # Optional: Number of posts to recommend
    max_communities: int = None,  # Optional: Number of communities to recommend
    max_users: int = None  # Optional: Number of users to recommend
):
    """
    Recommendation algorithm that fetches and ranks posts, communities, and users for a user.

    Args:
        user_id (str): ID of the user to recommend content for.
        max_posts (int): Maximum number of posts to recommend. If None, no posts are recommended.
        max_communities (int): Maximum number of communities to recommend. If None, no communities are recommended.
        max_users (int): Maximum number of users to recommend. If None, no users are recommended.

    Returns:
        dict: Recommended posts, communities, and users based on the provided arguments.
    """
    # Fetch user profile
    user = await user_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise ValueError("User not found")

    user_interests = user.get("interests", [])
    user_following = user.get("following", {}).get("users", [])
    user_bio = user.get("bio", "").lower()  # Normalize bio for matching
    recently_read_posts = user.get("recently_read_posts", [])
    now = datetime.utcnow()

    recommendations = {}

    # Helper to calculate post scores
    def calculate_post_score(post):
        score = 0
        # Boost for tags that match user interests
        for tag in post["tags"]:
            if tag in user_interests:
                score += 10
        # Likes, dislikes, and comments impact
        score += post["likes"]["count"] * 5
        score -= post["dislikes"]["count"] * 2
        score += len(post["comments"]) * 3
        # Freshness boost for posts created within the last 7 days
        days_since_posted = (now - post["created_on"]).days
        if days_since_posted <= 7:
            score += (7 - days_since_posted) * 2
        # Incorporate views, with diminishing returns for higher view counts
        if "views" in post:
            score += min(post["views"] // 10, 20)  # Add up to 20 points max for views, scaled by every 10 views
        return score

    # Fetch and process posts if max_posts is specified
    if max_posts is not None:
        interest_based_posts = await posts_collection.find({
            "tags": {"$in": user_interests}
        }).to_list(length=100)

        followed_users_posts = await posts_collection.find({
            "user_id": {"$in": user_following}
        }).to_list(length=50)

        trending_posts = await posts_collection.find({
            "$or": [
                {"likes.count": {"$gte": 50}},
                {"dislikes.count": {"$lte": 10}},
                {"views": {"$gte": 100}}  # Trending posts with high views
            ]
        }).sort("likes.count", DESCENDING).to_list(length=50)

        # Merge posts and remove duplicates (based on post ID)
        all_posts = {post["_id"]: post for post in (interest_based_posts + followed_users_posts + trending_posts)}
        all_posts = [post for post in all_posts.values() if post["_id"] not in recently_read_posts]

        # Rank posts based on the updated scoring system
        ranked_posts = sorted(all_posts, key=calculate_post_score, reverse=True)

        # Group posts by score and shuffle within each group
        grouped_posts = {}
        for post in ranked_posts:
            score = calculate_post_score(post)
            grouped_posts.setdefault(score, []).append(post)

        final_posts = []
        for score, posts in grouped_posts.items():
            random.shuffle(posts)
            final_posts.extend(posts)

        recommendations["recommended_posts"] = [
            {
                "post_id": post["post_id"],
                "heading": post["heading"],
                "tldr": post["tldr"],
                "description": post.get("description", None),
                "tags": post["tags"],
                "likes": post["likes"]["count"],
                "dislikes": post["dislikes"]["count"],
                "comments_count": len(post["comments"]),
                "views": post.get("views", 0),
                "created_on": post["created_on"].isoformat(),
            }
            for post in final_posts[:max_posts]
        ]

    # Fetch and process communities if max_communities is specified
    if max_communities is not None:
        recommended_communities = await communities_collection.find({
            "tags": {"$in": user_interests}
        }).sort([("member_count", DESCENDING), ("created_on", DESCENDING)]).to_list(length=100)

        community_set = set()
        ranked_communities = []
        for community in recommended_communities:
            if community["community_id"] not in community_set:
                community_set.add(community["community_id"])
                ranked_communities.append(community)

        recommendations["recommended_communities"] = [
            {
                "community_id": community["community_id"],
                "community_name": community["community_name"],
                "tags": community["tags"],
                "member_count": community["member_count"],
            }
            for community in ranked_communities[:max_communities]
        ]

    # Fetch and process users if max_users is specified
    if max_users is not None:
        def calculate_user_similarity_score(target_user):
            score = 0
            if target_user["_id"] in user_following:
                return -1
            target_interests = target_user.get("interests", [])
            score += len(set(user_interests) & set(target_interests)) * 10
            target_bio = target_user.get("bio", "").lower()
            for interest in user_interests:
                if interest.lower() in target_bio:
                    score += 5
            return score

        potential_users = await user_collection.find({
            "_id": {"$ne": ObjectId(user_id)},
            "$or": [
                {"interests": {"$in": user_interests}},
                {"bio": {"$regex": "|".join(user_interests), "$options": "i"}}
            ]
        }).to_list(length=100)

        scored_users = [(target_user, calculate_user_similarity_score(target_user)) for target_user in potential_users]
        scored_users = [user for user, score in scored_users if score > 0]
        scored_users.sort(key=lambda user: calculate_user_similarity_score(user), reverse=True)
        random.shuffle(scored_users)

        recommendations["recommended_users"] = [
            {
                "username": user["username"],
                "handle": user["handle"],
                "profile_picture": user.get("profile_picture", {}).get("url", ""),
            }
            for user in scored_users[:max_users]
        ]

    return recommendations