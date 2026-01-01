import re
import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from handlers.config import all_subcategories


def clean_text(text):
    """
    Cleans text by removing special characters, converting to lowercase, and trimming whitespace.
    
    Args:
        text (str): The input text to clean.
    
    Returns:
        str: The cleaned text.
    """
    text = re.sub(r"[^a-zA-Z0-9#\s]", "", text)  # Remove special characters
    text = text.lower().strip()  # Convert to lowercase and strip whitespace
    return text


def determine_tags(heading, tldr, all_subcategories, min_tags=4, max_tags=6):
    """
    Determines the most relevant tags for a post based on its heading and TLDR.
    
    Args:
        heading (str): The heading of the post.
        tldr (str): The TLDR of the post.
        all_subcategories (list): A list of available tags (e.g., #blockchain, #python).
        min_tags (int): Minimum number of tags to return.
        max_tags (int): Maximum number of tags to return.
    
    Returns:
        list: A randomly selected list of relevant tags (between min_tags and max_tags).
    """
    # Combine heading and TLDR for input context
    post_content = clean_text(heading + " " + tldr)

    # Clean all subcategories
    cleaned_tags = [clean_text(tag) for tag in all_subcategories]

    # TF-IDF Vectorization
    tfidf_vectorizer = TfidfVectorizer()
    vectors = tfidf_vectorizer.fit_transform([post_content] + cleaned_tags)
    
    # Compute cosine similarity between the post content and each tag
    post_vector = vectors[0]  # The vector for the input post
    tag_vectors = vectors[1:]  # The vectors for the tags
    similarities = cosine_similarity(post_vector, tag_vectors).flatten()

    # Rank tags by similarity score
    tag_scores = list(zip(all_subcategories, similarities))
    sorted_tags = sorted(tag_scores, key=lambda x: x[1], reverse=True)

    # Select relevant tags with similarity above 0.1
    relevant_tags = [tag for tag, score in sorted_tags if score > 0.1]

    # Randomly select the number of tags to return within the range [min_tags, max_tags]
    num_tags_to_return = random.randint(min_tags, max_tags)

    # Ensure the number of tags to return does not exceed available relevant tags
    selected_tags = relevant_tags[:num_tags_to_return]

    # If there aren't enough relevant tags, pad with lower-ranked tags
    if len(selected_tags) < num_tags_to_return:
        remaining_tags = [tag for tag, _ in sorted_tags if tag not in selected_tags]
        selected_tags += remaining_tags[:num_tags_to_return - len(selected_tags)]

    return selected_tags