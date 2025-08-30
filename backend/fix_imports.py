#!/usr/bin/env python3
"""
Script to fix relative import issues in agent files
"""
import os
import re

def fix_agent_imports(file_path):
    """Fix relative imports in agent files"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Pattern to match relative tool imports
    pattern = r'from \.\.tools\.(\w+) import (\w+)'
    
    def replacement(match):
        module = match.group(1)
        tool = match.group(2)
        return f"""try:
    from tools.{module} import {tool}
except ImportError:
    try:
        from backend.tools.{module} import {tool}
    except ImportError:
        from ..tools.{module} import {tool}"""
    
    # Apply replacements
    new_content = re.sub(pattern, replacement, content)
    
    if new_content != content:
        with open(file_path, 'w') as f:
            f.write(new_content)
        print(f"Fixed imports in {file_path}")
        return True
    return False

def main():
    agent_files = [
        'agents/analytics.py',
        'agents/business_operations.py', 
        'agents/player_development.py',
        'agents/team_gms.py'
    ]
    
    for file_path in agent_files:
        if os.path.exists(file_path):
            fix_agent_imports(file_path)
        else:
            print(f"Warning: {file_path} not found")

if __name__ == "__main__":
    main()