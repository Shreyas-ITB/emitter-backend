import json
import ollama

def generate_role_tag(tags: list) -> dict:
    """
    Uses Ollama to generate achievement role names and tag names based on a list of tags.
    
    Args:
        tags (list): A list of tags related to different topics (e.g., ['JavaScript', 'AI', 'Python']).
    
    Returns:
        dict: A dictionary containing the generated role name and tag name.
    """
    try:
        # Construct the prompt for Ollama
        prompt = f"""
        You are an expert in generating achievement roles and tag names based on a list of tags.
        Rules are: Generate unique achievement roles and tag names for each topic from the tags provided.
        For each tag, generate one achievement role and one tag name.

        Example roles:
        "Postworm"
        "Commentator Supreme"
        "Tag Titan"

        Example tag names:
        "Top reader in #GitHub"
        "Leading voice in #Python"
        "Rising star in #AI"
        
        Task: Based on the following tags, generate an achievement role name and a corresponding tag name.
        Tags: {', '.join(tags)}
        
        Return your output in the following JSON format:
        {{
            "roles": ["Generated Role for Tag1", "Generated Role for Tag2", "Generated Role for Tag3", ...],
            "tagnames": ["Generated Tag Name for Tag1", "Generated Tag Name for Tag2", "Generated Tag Name for Tag3", ...]
        }}
        """

        # Send the prompt to Ollama and get the response
        response = ollama.generate(model="llava:7b", prompt=prompt)
        if 'response' in response:
            result = response['response']  
            # Assuming the response is a string in JSON format, try to parse it
            try:
                result_dict = json.loads(result)
                return result_dict
            except json.JSONDecodeError as e:
                return {"error": f"Failed to decode JSON: {str(e)}"}
        else:
            return {"error": "No response field found in the Ollama output."}

    except Exception as e:
        return {"error": str(e)}