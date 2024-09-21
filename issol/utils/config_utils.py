import os
import json
from pathlib import Path

CONFIG_FILE = Path.home() / '.issol_config.json'

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

def get_or_prompt_token(token_name, prompt_message):
    config = load_config()
    token = os.environ.get(token_name) or config.get(token_name)
    
    if not token:
        token = input(f"{prompt_message}: ").strip()
        config[token_name] = token
        save_config(config)
        print(f"{token_name} has been saved to {CONFIG_FILE}")
    
    return token

def setup_tokens():
    github_token = get_or_prompt_token(
        'GITHUB_TOKEN',
        "Please enter your GitHub Personal Access Token"
    )
    anthropic_token = get_or_prompt_token(
        'ANTHROPIC_API_KEY',
        "Please enter your Anthropic API Key"
    )
    
    os.environ['GITHUB_TOKEN'] = github_token
    os.environ['ANTHROPIC_API_KEY'] = anthropic_token

    return github_token, anthropic_token