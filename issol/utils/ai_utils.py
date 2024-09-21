import os
import sys
from anthropic import Anthropic
from .config_utils import get_or_prompt_token

def get_anthropic_client():
    anthropic_api_key = get_or_prompt_token('ANTHROPIC_API_KEY', "Please enter your Anthropic API Key")
    if anthropic_api_key:
        return Anthropic(api_key=anthropic_api_key)
    else:
        print("Failed to obtain Anthropic API Key. Exiting.")
        sys.exit(1)

anthropic_client = get_anthropic_client()

def generate_code(system_prompt, human_prompt):
    try:
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=4000,
            temperature=0.1,
            system=system_prompt,
            messages=[
                {"role": "user", "content": human_prompt}
            ]
        )
        return response.content[0].text
    except Exception as e:
        print(f"Error generating code: {str(e)}")
        return ""