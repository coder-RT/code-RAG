"""
Architecture Analyzer - Analyze system architecture and module responsibilities
"""

import os
import re
from typing import Dict, List, Optional
from pathlib import Path

from langchain_openai import ChatOpenAI
from app.core.config import settings


class ArchitectureAnalyzer:
    """
    Analyzes codebase architecture to identify modules,
    layers, patterns, and responsibilities.
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=0.1
        )
    
    async def analyze(self, path: str, analysis_type: str = "full") -> Dict:
        """
        Perform architecture analysis on a codebase.
        """
        results = {}
        
        if analysis_type in ["full", "modules"]:
            results["modules"] = await self.identify_modules(path)
        
        if analysis_type in ["full", "layers"]:
            results["layers"] = await self.identify_layers(path)
        
        if analysis_type in ["full", "dependencies"]:
            results["dependencies"] = await self._analyze_dependencies(path)
        
        if analysis_type == "full":
            results["patterns"] = await self.detect_patterns(path)
            results["summary"] = await self._generate_summary(results)
        
        return results
    
    async def identify_modules(self, path: str) -> List[Dict]:
        """
        Identify modules/packages in the codebase and their responsibilities.
        """
        modules = []
        
        # Look for common module indicators
        for root, dirs, files in os.walk(path):
            # Skip common ignored directories
            dirs[:] = [d for d in dirs if d not in [
                'node_modules', '__pycache__', 'venv', '.git', 
                'dist', 'build', '.next', 'test', 'tests'
            ]]
            
            relative_root = os.path.relpath(root, path)
            if relative_root == '.':
                relative_root = ''
            
            # Check for module indicators
            has_init = '__init__.py' in files
            has_index = any(f.startswith('index.') for f in files)
            has_mod = 'mod.rs' in files
            has_package = 'package.json' in files
            
            if has_init or has_index or has_mod or has_package or root == path:
                module_files = [f for f in files if any(
                    f.endswith(ext) for ext in settings.SUPPORTED_EXTENSIONS
                )]
                
                if module_files or root == path:
                    module_info = {
                        "name": os.path.basename(root) or "root",
                        "path": relative_root or ".",
                        "type": self._detect_module_type(root, files),
                        "files": module_files[:10],  # Limit files shown
                        "description": await self._describe_module(root, module_files[:5])
                    }
                    modules.append(module_info)
        
        return modules
    
    async def identify_layers(self, path: str) -> List[Dict]:
        """
        Identify architectural layers (presentation, business, data, etc.)
        """
        layer_patterns = {
            "presentation": ["ui", "views", "components", "pages", "screens", "frontend"],
            "api": ["api", "routes", "endpoints", "controllers", "handlers"],
            "business": ["services", "domain", "core", "business", "logic"],
            "data": ["models", "repositories", "database", "db", "data", "entities"],
            "infrastructure": ["infra", "infrastructure", "terraform", "deploy", "config"],
            "utilities": ["utils", "helpers", "common", "shared", "lib"]
        }
        
        layers = []
        
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in [
                'node_modules', '__pycache__', 'venv', '.git', 'dist', 'build'
            ]]
            
            dir_name = os.path.basename(root).lower()
            
            for layer_name, patterns in layer_patterns.items():
                if any(pattern in dir_name for pattern in patterns):
                    relative_path = os.path.relpath(root, path)
                    
                    # Check if layer already exists
                    existing = next(
                        (l for l in layers if l["name"] == layer_name),
                        None
                    )
                    
                    if existing:
                        existing["paths"].append(relative_path)
                    else:
                        layers.append({
                            "name": layer_name,
                            "paths": [relative_path],
                            "description": f"Contains {layer_name} layer components"
                        })
        
        return layers
    
    async def detect_patterns(self, path: str) -> List[Dict]:
        """
        Detect architectural and design patterns in the codebase.
        """
        patterns_found = []
        
        # Collect code samples for pattern detection
        code_samples = await self._collect_code_samples(path)
        
        prompt = f"""Analyze these code samples and identify architectural and design patterns used.

Code Samples:
{code_samples}

Identify patterns such as:
- Architectural patterns (MVC, MVVM, Clean Architecture, Hexagonal, etc.)
- Design patterns (Factory, Singleton, Observer, Repository, etc.)
- API patterns (REST, GraphQL, RPC)
- Data patterns (DAO, Active Record, Repository)

For each pattern found, provide:
1. Pattern name
2. Where it's implemented (files/modules)
3. Brief explanation of how it's used

Format as a structured list."""

        response = await self.llm.ainvoke(prompt)
        
        # Parse patterns from response
        patterns_found.append({
            "analysis": response.content
        })
        
        return patterns_found
    
    async def explain_module(self, path: str) -> Dict:
        """
        Get a detailed explanation of what a specific module does.
        """
        if not os.path.exists(path):
            raise ValueError(f"Path not found: {path}")
        
        files = []
        if os.path.isdir(path):
            for f in os.listdir(path):
                file_path = os.path.join(path, f)
                if os.path.isfile(file_path):
                    ext = os.path.splitext(f)[1]
                    if ext in settings.SUPPORTED_EXTENSIONS:
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as fp:
                                content = fp.read()[:3000]
                            files.append({"name": f, "content": content})
                        except:
                            continue
        else:
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                files.append({"name": os.path.basename(path), "content": content})
            except Exception as e:
                return {"error": str(e)}
        
        file_contents = "\n\n".join([
            f"=== {f['name']} ===\n{f['content']}" for f in files[:5]
        ])
        
        prompt = f"""Analyze this module and explain its purpose and responsibilities.

Module Path: {path}

Files:
{file_contents}

Provide:
1. **Purpose**: What is the main responsibility of this module?
2. **Components**: What are the key classes/functions?
3. **Dependencies**: What does it depend on?
4. **Consumers**: Who/what would use this module?
5. **Integration**: How does it fit into the overall architecture?"""

        response = await self.llm.ainvoke(prompt)
        
        return {
            "path": path,
            "files_analyzed": len(files),
            "explanation": response.content
        }
    
    async def _analyze_dependencies(self, path: str) -> Dict:
        """Analyze module dependencies."""
        dependencies = {
            "internal": [],
            "external": []
        }
        
        import_patterns = {
            "python": r"^(?:from|import)\s+([\w\.]+)",
            "javascript": r"(?:import|require)\s*\(?\s*['\"]([^'\"]+)['\"]",
            "typescript": r"import\s+.*?from\s+['\"]([^'\"]+)['\"]",
        }
        
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in [
                'node_modules', '__pycache__', 'venv', '.git'
            ]]
            
            for file in files:
                file_path = os.path.join(root, file)
                ext = os.path.splitext(file)[1]
                
                if ext == '.py':
                    pattern = import_patterns["python"]
                elif ext in ['.js', '.jsx']:
                    pattern = import_patterns["javascript"]
                elif ext in ['.ts', '.tsx']:
                    pattern = import_patterns["typescript"]
                else:
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    imports = re.findall(pattern, content, re.MULTILINE)
                    
                    for imp in imports:
                        if imp.startswith('.') or imp.startswith('/'):
                            dependencies["internal"].append(imp)
                        else:
                            dependencies["external"].append(imp)
                except:
                    continue
        
        # Deduplicate
        dependencies["internal"] = list(set(dependencies["internal"]))
        dependencies["external"] = list(set(dependencies["external"]))
        
        return dependencies
    
    async def _generate_summary(self, results: Dict) -> str:
        """Generate a summary of the architecture analysis."""
        prompt = f"""Based on this architecture analysis, provide a concise summary:

Modules: {len(results.get('modules', []))} found
Layers: {[l['name'] for l in results.get('layers', [])]}
Dependencies: {len(results.get('dependencies', {}).get('external', []))} external

Provide a 2-3 paragraph summary of:
1. Overall architecture style
2. Key modules and their relationships
3. Notable patterns or practices"""

        response = await self.llm.ainvoke(prompt)
        return response.content
    
    def _detect_module_type(self, path: str, files: List[str]) -> str:
        """Detect the type of module based on files present."""
        if '__init__.py' in files:
            return "python_package"
        if 'package.json' in files:
            return "npm_package"
        if 'Cargo.toml' in files:
            return "rust_crate"
        if 'go.mod' in files:
            return "go_module"
        if any(f.endswith('.tf') for f in files):
            return "terraform_module"
        return "directory"
    
    async def _describe_module(self, path: str, files: List[str]) -> str:
        """Generate a brief description of a module."""
        if not files:
            return "Empty module or directory"
        
        # Read first file to get context
        for f in files:
            file_path = os.path.join(path, f)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as fp:
                    content = fp.read()[:1000]
                
                # Simple heuristic for description
                if 'test' in f.lower():
                    return "Test module"
                if 'config' in f.lower():
                    return "Configuration module"
                if 'util' in f.lower() or 'helper' in f.lower():
                    return "Utility/helper functions"
                if 'model' in f.lower():
                    return "Data models"
                if 'route' in f.lower() or 'controller' in f.lower():
                    return "API routes/controllers"
                if 'service' in f.lower():
                    return "Business logic services"
                
                return "Code module"
            except:
                continue
        
        return "Unknown module type"
    
    async def _collect_code_samples(self, path: str, max_samples: int = 10) -> str:
        """Collect representative code samples for analysis."""
        samples = []
        count = 0
        
        for root, dirs, files in os.walk(path):
            if count >= max_samples:
                break
            
            dirs[:] = [d for d in dirs if d not in [
                'node_modules', '__pycache__', 'venv', '.git', 'test', 'tests'
            ]]
            
            for f in files:
                if count >= max_samples:
                    break
                
                ext = os.path.splitext(f)[1]
                if ext not in settings.SUPPORTED_EXTENSIONS:
                    continue
                
                file_path = os.path.join(root, f)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as fp:
                        content = fp.read()[:2000]
                    
                    relative_path = os.path.relpath(file_path, path)
                    samples.append(f"=== {relative_path} ===\n{content}")
                    count += 1
                except:
                    continue
        
        return "\n\n".join(samples)

