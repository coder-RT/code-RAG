"""
Code Analyzer - Analyze and explain code structure
"""

import os
from typing import Dict, List, Optional
from pathlib import Path

from langchain_openai import ChatOpenAI
from app.core.config import settings


class CodeAnalyzer:
    """
    Analyzes code files and directories to provide explanations
    and structural information.
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=0.1
        )
    
    async def explain(self, path: str, detail_level: str = "summary") -> str:
        """
        Generate an explanation of what a file or directory does.
        """
        if os.path.isfile(path):
            return await self._explain_file(path, detail_level)
        elif os.path.isdir(path):
            return await self._explain_directory(path, detail_level)
        else:
            raise ValueError(f"Invalid path: {path}")
    
    async def _explain_file(self, file_path: str, detail_level: str) -> str:
        """Explain a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            return f"Error reading file: {e}"
        
        # Truncate if too long
        if len(content) > 15000:
            content = content[:15000] + "\n...[truncated]..."
        
        prompt = f"""Analyze this code file and provide a {detail_level} explanation.

File: {os.path.basename(file_path)}
Path: {file_path}

```
{content}
```

Provide:
1. What this file does (main purpose)
2. Key functions/classes and their roles
3. Dependencies and imports
4. How it fits into a larger system (if apparent)

Detail level: {detail_level}"""

        response = await self.llm.ainvoke(prompt)
        return response.content
    
    async def _explain_directory(self, dir_path: str, detail_level: str) -> str:
        """Explain a directory and its contents."""
        structure = self.get_structure(dir_path)
        
        # Get a sample of important files
        important_files = self._find_important_files(dir_path)
        file_samples = []
        
        for file_path in important_files[:5]:  # Limit to 5 files
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()[:2000]  # First 2000 chars
                file_samples.append({
                    "path": os.path.relpath(file_path, dir_path),
                    "content": content
                })
            except:
                continue
        
        prompt = f"""Analyze this directory structure and provide a {detail_level} explanation.

Directory: {dir_path}

Structure:
{self._format_structure(structure)}

Sample Files:
{self._format_samples(file_samples)}

Provide:
1. What this directory/module does (main purpose)
2. How the files are organized
3. Key components and their responsibilities
4. How they work together

Detail level: {detail_level}"""

        response = await self.llm.ainvoke(prompt)
        return response.content
    
    def get_structure(self, path: str, max_depth: int = 4) -> Dict:
        """
        Get the directory structure as a nested dictionary.
        """
        def build_tree(current_path: str, depth: int) -> Dict:
            if depth > max_depth:
                return {"...": "max depth reached"}
            
            result = {}
            
            try:
                entries = sorted(os.listdir(current_path))
            except PermissionError:
                return {"error": "permission denied"}
            
            for entry in entries:
                # Skip hidden and common ignore patterns
                if entry.startswith('.') or entry in [
                    'node_modules', '__pycache__', 'venv', '.git', 
                    'dist', 'build', '.next'
                ]:
                    continue
                
                full_path = os.path.join(current_path, entry)
                
                if os.path.isdir(full_path):
                    result[entry + "/"] = build_tree(full_path, depth + 1)
                else:
                    ext = os.path.splitext(entry)[1]
                    result[entry] = ext or "file"
            
            return result
        
        return {os.path.basename(path) + "/": build_tree(path, 0)}
    
    def _find_important_files(self, dir_path: str) -> List[str]:
        """Find the most important files in a directory."""
        important_patterns = [
            'main.py', 'app.py', 'index.ts', 'index.js', 'index.tsx',
            'mod.rs', 'lib.rs', 'main.go', 'main.rs',
            'package.json', 'requirements.txt', 'Cargo.toml',
            'README.md', 'setup.py', 'pyproject.toml',
            'main.tf', 'variables.tf'
        ]
        
        found_files = []
        
        for root, dirs, files in os.walk(dir_path):
            # Skip common ignored directories
            dirs[:] = [d for d in dirs if d not in [
                'node_modules', '__pycache__', 'venv', '.git', 'dist', 'build'
            ]]
            
            for pattern in important_patterns:
                if pattern in files:
                    found_files.append(os.path.join(root, pattern))
        
        return found_files
    
    def _format_structure(self, structure: Dict, indent: int = 0) -> str:
        """Format structure dict as tree string."""
        lines = []
        for key, value in structure.items():
            prefix = "  " * indent
            if isinstance(value, dict):
                lines.append(f"{prefix}{key}")
                lines.append(self._format_structure(value, indent + 1))
            else:
                lines.append(f"{prefix}{key}")
        return "\n".join(lines)
    
    def _format_samples(self, samples: List[Dict]) -> str:
        """Format file samples for the prompt."""
        result = []
        for sample in samples:
            result.append(f"--- {sample['path']} ---")
            result.append(sample['content'])
            result.append("")
        return "\n".join(result)

