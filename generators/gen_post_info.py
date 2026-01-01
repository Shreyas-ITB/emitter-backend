import ollama
import json
import re


def truncate_text_to_word_limit(text, word_limit=490):
    """
    Truncates the given text to the specified word limit while ensuring it ends with a complete sentence.

    Args:
        text (str): The input text to truncate.
        word_limit (int): The maximum allowed number of words.

    Returns:
        str: The truncated text ending with a complete sentence.
    """
    words = text.split()
    if len(words) <= word_limit:
        return text

    truncated_text = " ".join(words[:word_limit])
    # Ensure the text ends with a complete sentence by finding the last punctuation mark
    sentence_end_match = re.search(r'[.!?](?=[^.!?]*$)', truncated_text)
    if sentence_end_match:
        end_index = sentence_end_match.end()
        return truncated_text[:end_index].strip()
    else:
        # Fallback: if no sentence boundary is found, return the entire truncated text
        return truncated_text.strip()


# Function to generate tags and TLDR using Ollama
def process_post(heading: str, description: str):
    """
    Uses Ollama to generate tags and a TLDR for a post based on its heading and description.

    Args:
        heading (str): The heading of the post.
        description (str): The description of the post.

    Returns:
        dict: A dictionary containing generated tags and TLDR.
    """
    try:
        # Construct the prompt for Ollama
        prompt = f"""
        You are an expert tag generator and summarizer.
        Rules are: you have to generate six or more tags. Strictly follow the rules.
        Task 1: Generate six or more relevant and accurate tags for a blog post based on the following details:
        - Heading: "{heading}"
        - Description: "{description}"
        
        Task 2: Create a TLDR (Too Long; Didn't Read) version of the description, focusing on its main points, should be under 400 characters strictly follow the character limit.
        
        Return your output in the following JSON format:
        {{
            "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8"],
            "tldr": "A very short, focused summary of the description."
        }}
        """

        # Send the prompt to Ollama and get the response
        response = ollama.generate(model="llava:7b", prompt=prompt)
        
        if 'response' in response:
            result = response['response']
            
            # Assuming the response is a string in JSON format, try to parse it
            try:
                result_dict = json.loads(result)

                # Truncate TLDR to 490 words and ensure it ends with a complete sentence
                if "tldr" in result_dict:
                    result_dict["tldr"] = truncate_text_to_word_limit(result_dict["tldr"], word_limit=400)

                return result_dict
            except json.JSONDecodeError as e:
                return {"error": f"Failed to decode JSON: {str(e)}"}
        else:
            return {"error": "No response field found in the Ollama output."}

    except Exception as e:
        return {"error": str(e)}


# Function to generate tags and TLDR using Ollama based on heading only
def process_heading(heading: str):
    """
    Uses Ollama to generate tags and a TLDR for a post based on its heading.

    Args:
        heading (str): The heading of the post.

    Returns:
        dict: A dictionary containing generated tags and TLDR.
    """
    try:
        # Construct the prompt for Ollama
        prompt = f"""
        You are an expert tag generator and summarizer.
        Rules are: you have to generate six or more tags. Strictly follow the rules.
        Task 1: Generate six or more relevant and accurate tags for a blog post based on its heading.
        Task 2: Create a TLDR (Too Long; Didn't Read) version of the heading, summarizing its essence, should be under 400 characters strictly follow the character limit.

        Heading: "{heading}"
        
        Return your output in the following JSON format:
        {{
            "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8"],
            "tldr": "A concise summary of the heading."
        }}
        """

        # Send the prompt to Ollama and get the response
        response = ollama.generate(model="llava:7b", prompt=prompt)

        if 'response' in response:
            result = response['response']
            
            # Assuming the response is a string in JSON format, try to parse it
            try:
                result_dict = json.loads(result)

                # Truncate TLDR to 490 words and ensure it ends with a complete sentence
                if "tldr" in result_dict:
                    result_dict["tldr"] = truncate_text_to_word_limit(result_dict["tldr"], word_limit=400)

                return result_dict
            except json.JSONDecodeError as e:
                return {"error": f"Failed to decode JSON: {str(e)}"}
        else:
            return {"error": "No response field found in the Ollama output."}

    except Exception as e:
        return {"error": str(e)}
