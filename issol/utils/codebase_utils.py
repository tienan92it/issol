import os
import logging

def summarize_codebase():
    logging.info("Summarizing codebase...")
    summary = {
        "total_files": 0,
        "total_lines": 0,
        "file_types": {}
    }

    for root, _, files in os.walk('.'):
        for file in files:
            if file.startswith('.') or 'venv' in root:
                continue

            file_path = os.path.join(root, file)
            _, extension = os.path.splitext(file)
            
            summary["total_files"] += 1
            summary["file_types"][extension] = summary["file_types"].get(extension, 0) + 1

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    summary["total_lines"] += len(lines)
            except Exception as e:
                logging.warning(f"Could not read file {file_path}: {str(e)}")

    return f"""Codebase Summary:
Total Files: {summary['total_files']}
Total Lines of Code: {summary['total_lines']}
File Types:
{chr(10).join([f"  {ext}: {count}" for ext, count in summary['file_types'].items()])}
"""