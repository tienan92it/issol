import os
import logging
import json
from collections import Counter
import re
from ..utils.ai_utils import generate_code

CODEBASE_CONTEXT_DIR = '.codebase_context'

def run():
    logging.info("Starting codebase context generation...")
    os.makedirs(CODEBASE_CONTEXT_DIR, exist_ok=True)
    
    project_info = gather_project_info()
    tech_stack_info = identify_tech_stack(project_info)
    
    generate_tech_stack_file(tech_stack_info)
    
    logging.info("Codebase context generation complete.")

def gather_project_info():
    project_info = {
        'structure': get_project_structure(),
        'config_files': parse_config_files(),
        'readme_content': get_readme_content(),
        'file_extensions': count_file_extensions(),
        'import_statements': gather_import_statements()
    }
    return project_info

def get_project_structure():
    structure = []
    for root, dirs, files in os.walk('.'):
        level = root.replace('.', '').count(os.sep)
        indent = ' ' * 4 * level
        subindent = ' ' * 4 * (level + 1)
        structure.append(f'{indent}{os.path.basename(root)}/')
        for f in files:
            structure.append(f'{subindent}{f}')
    return '\n'.join(structure)

def parse_config_files():
    config_files = {}
    for file in ['package.json', 'requirements.txt', 'Gemfile', 'Dockerfile']:
        if os.path.exists(file):
            with open(file, 'r') as f:
                config_files[file] = f.read()
    return config_files

def get_readme_content():
    readme_files = ['README.md', 'README.txt', 'README']
    for file in readme_files:
        if os.path.exists(file):
            with open(file, 'r') as f:
                return f.read()
    return ""

def count_file_extensions():
    extensions = Counter()
    for root, _, files in os.walk('.'):
        for file in files:
            _, ext = os.path.splitext(file)
            if ext:
                extensions[ext] += 1
    return dict(extensions)

def gather_import_statements(sample_size=10):
    import_statements = []
    for root, _, files in os.walk('.'):
        for file in files:
            if len(import_statements) >= sample_size:
                break
            if file.endswith(('.js', '.ts', '.py', '.rb')):
                with open(os.path.join(root, file), 'r') as f:
                    content = f.read()
                    imports = re.findall(r'^(import|require|from).*', content, re.MULTILINE)
                    import_statements.extend(imports[:5])  # Limit to 5 imports per file
    return import_statements

def identify_tech_stack(project_info):
    system_prompt = """You are an AI assistant tasked with identifying the tech stack of a software project. 
    Analyze the provided project information and determine the technologies used."""
    
    human_prompt = f"""Based on the following project information, identify the tech stack including:
    - Programming languages
    - Frameworks and libraries
    - Databases
    - DevOps tools
    - Any other relevant technologies

    Project Structure:
    {project_info['structure'][:500]}...

    Configuration Files:
    {json.dumps(project_info['config_files'], indent=2)}

    README Content:
    {project_info['readme_content'][:500]}...

    File Extensions:
    {json.dumps(project_info['file_extensions'], indent=2)}

    Sample Import Statements:
    {json.dumps(project_info['import_statements'], indent=2)}

    Please provide a detailed tech stack identification, explaining your reasoning for each technology identified."""

    return generate_code(system_prompt, human_prompt)

def generate_tech_stack_file(tech_stack_info):
    file_path = os.path.join(CODEBASE_CONTEXT_DIR, "tech_stack.md")
    with open(file_path, 'w') as f:
        f.write("# Tech Stack Identification\n\n")
        f.write(tech_stack_info)
    logging.info(f"Tech stack information written to {file_path}")