"""
Loader - Load files by type with appropriate parsing
"""

import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
from enum import Enum
import re


class FileType(str, Enum):
    """Supported file types"""
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    TERRAFORM = "terraform"
    MARKDOWN = "markdown"
    YAML = "yaml"
    JSON = "json"
    GO = "go"
    RUST = "rust"
    SQL = "sql"
    DOCKERFILE = "dockerfile"
    UNKNOWN = "unknown"


@dataclass
class LoadedFile:
    """A loaded file with metadata"""
    path: str
    relative_path: str
    content: str
    file_type: FileType
    extension: str
    size_bytes: int
    metadata: Dict[str, Any]


class FileLoader:
    """
    Loads files from a codebase with type detection and metadata extraction.
    """
    
    # Extension to FileType mapping
    EXTENSION_MAP = {
        ".py": FileType.PYTHON,
        ".pyi": FileType.PYTHON,
        ".ts": FileType.TYPESCRIPT,
        ".tsx": FileType.TYPESCRIPT,
        ".js": FileType.JAVASCRIPT,
        ".jsx": FileType.JAVASCRIPT,
        ".mjs": FileType.JAVASCRIPT,
        ".tf": FileType.TERRAFORM,
        ".tfvars": FileType.TERRAFORM,
        ".md": FileType.MARKDOWN,
        ".mdx": FileType.MARKDOWN,
        ".yaml": FileType.YAML,
        ".yml": FileType.YAML,
        ".json": FileType.JSON,
        ".go": FileType.GO,
        ".rs": FileType.RUST,
        ".sql": FileType.SQL,
    }
    
    # Special filenames
    SPECIAL_FILES = {
        "Dockerfile": FileType.DOCKERFILE,
        "Makefile": FileType.UNKNOWN,  # Could add support
        "docker-compose.yml": FileType.YAML,
        "docker-compose.yaml": FileType.YAML,
    }
    
    # Default directories to exclude
    DEFAULT_EXCLUDE = [
        "node_modules", ".git", "__pycache__", "venv", ".venv",
        "dist", "build", ".next", ".terraform", "vendor",
        ".idea", ".vscode", "coverage", ".pytest_cache",
        ".mypy_cache", ".tox", "eggs", "*.egg-info",
        ".cache", ".gradle", "target"
    ]
    
    def __init__(
        self,
        max_file_size_kb: int = 500,
        exclude_patterns: Optional[List[str]] = None
    ):
        self.max_file_size_kb = max_file_size_kb
        self.exclude_patterns = exclude_patterns or self.DEFAULT_EXCLUDE
    
    def load_directory(self, path: str) -> List[LoadedFile]:
        """
        Load all supported files from a directory.
        
        Args:
            path: Path to directory to load
            
        Returns:
            List of LoadedFile objects
        """
        files = []
        base_path = Path(path)
        
        if not base_path.exists():
            raise ValueError(f"Path does not exist: {path}")
        
        if not base_path.is_dir():
            # Single file
            loaded = self.load_file(str(base_path), str(base_path.parent))
            return [loaded] if loaded else []
        
        for file_path in self._walk_directory(base_path):
            loaded = self.load_file(str(file_path), str(base_path))
            if loaded:
                files.append(loaded)
        
        return files
    
    def load_file(self, file_path: str, base_path: str = "") -> Optional[LoadedFile]:
        """
        Load a single file with metadata.
        
        Args:
            file_path: Path to the file
            base_path: Base path for computing relative path
            
        Returns:
            LoadedFile or None if file should be skipped
        """
        path = Path(file_path)
        
        # Check if file exists
        if not path.exists() or not path.is_file():
            return None
        
        # Check file size
        size = path.stat().st_size
        if size > self.max_file_size_kb * 1024:
            return None
        
        # Skip empty files
        if size == 0:
            return None
        
        # Detect file type
        file_type = self._detect_file_type(path)
        
        if file_type == FileType.UNKNOWN:
            return None
        
        # Read content
        try:
            content = path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            return None
        
        # Skip if content is empty after reading
        if not content.strip():
            return None
        
        # Build relative path
        if base_path:
            try:
                relative_path = str(path.relative_to(base_path))
            except ValueError:
                relative_path = path.name
        else:
            relative_path = path.name
        
        # Extract metadata based on file type
        metadata = self._extract_metadata(content, file_type, path)
        
        return LoadedFile(
            path=str(path.absolute()),
            relative_path=relative_path,
            content=content,
            file_type=file_type,
            extension=path.suffix.lower(),
            size_bytes=size,
            metadata=metadata
        )
    
    def _walk_directory(self, base_path: Path):
        """Walk directory, respecting exclude patterns."""
        for root, dirs, files in os.walk(base_path):
            # Filter excluded directories (modify in place)
            dirs[:] = [d for d in dirs if not self._should_exclude(d)]
            
            for file in files:
                # Skip hidden files
                if file.startswith('.'):
                    continue
                
                file_path = Path(root) / file
                
                # Check if it's a supported file
                if self._detect_file_type(file_path) != FileType.UNKNOWN:
                    yield file_path
    
    def _should_exclude(self, name: str) -> bool:
        """Check if a directory should be excluded."""
        if name.startswith('.'):
            return True
        return name in self.exclude_patterns
    
    def _detect_file_type(self, path: Path) -> FileType:
        """Detect the file type from path."""
        # Check special filenames first
        if path.name in self.SPECIAL_FILES:
            return self.SPECIAL_FILES[path.name]
        
        # Check by extension
        ext = path.suffix.lower()
        return self.EXTENSION_MAP.get(ext, FileType.UNKNOWN)
    
    def _extract_metadata(
        self,
        content: str,
        file_type: FileType,
        path: Path
    ) -> Dict[str, Any]:
        """Extract file-type-specific metadata."""
        metadata = {
            "filename": path.name,
            "directory": str(path.parent.name),
            "full_directory": str(path.parent),
        }
        
        if file_type == FileType.PYTHON:
            metadata.update(self._extract_python_metadata(content))
        elif file_type == FileType.TERRAFORM:
            metadata.update(self._extract_terraform_metadata(content))
        elif file_type in [FileType.TYPESCRIPT, FileType.JAVASCRIPT]:
            metadata.update(self._extract_js_metadata(content))
        elif file_type == FileType.MARKDOWN:
            metadata.update(self._extract_markdown_metadata(content))
        elif file_type == FileType.YAML:
            metadata.update(self._extract_yaml_metadata(content))
        elif file_type == FileType.GO:
            metadata.update(self._extract_go_metadata(content))
        elif file_type == FileType.RUST:
            metadata.update(self._extract_rust_metadata(content))
        
        return metadata
    
    def _extract_python_metadata(self, content: str) -> Dict:
        """Extract Python-specific metadata."""
        metadata = {}
        
        # Find imports
        imports = re.findall(r'^(?:from|import)\s+([\w\.]+)', content, re.MULTILINE)
        metadata["imports"] = list(set(imports))[:20]
        
        # Find classes
        classes = re.findall(r'^class\s+(\w+)', content, re.MULTILINE)
        metadata["classes"] = classes
        
        # Find functions (top-level and methods)
        functions = re.findall(r'^(?:async\s+)?def\s+(\w+)', content, re.MULTILINE)
        metadata["functions"] = functions[:30]
        
        # Find decorators
        decorators = re.findall(r'^@(\w+)', content, re.MULTILINE)
        metadata["decorators"] = list(set(decorators))
        
        # Check for docstring
        if content.strip().startswith('"""') or content.strip().startswith("'''"):
            # Extract first docstring
            match = re.match(r'^["\']{{3}}(.*?)["\']{{3}}', content.strip(), re.DOTALL)
            if match:
                metadata["module_docstring"] = match.group(1)[:200]
        
        # Detect if it's a test file
        if 'test_' in metadata.get("filename", "") or '_test.py' in metadata.get("filename", ""):
            metadata["is_test"] = True
        
        return metadata
    
    def _extract_terraform_metadata(self, content: str) -> Dict:
        """Extract Terraform-specific metadata."""
        metadata = {}
        
        # Find resources
        resources = re.findall(r'resource\s+"([^"]+)"\s+"([^"]+)"', content)
        metadata["resources"] = [{"type": r[0], "name": r[1]} for r in resources]
        
        # Find modules
        modules = re.findall(r'module\s+"([^"]+)"', content)
        metadata["modules"] = modules
        
        # Find variables
        variables = re.findall(r'variable\s+"([^"]+)"', content)
        metadata["variables"] = variables
        
        # Find outputs
        outputs = re.findall(r'output\s+"([^"]+)"', content)
        metadata["outputs"] = outputs
        
        # Find data sources
        data_sources = re.findall(r'data\s+"([^"]+)"\s+"([^"]+)"', content)
        metadata["data_sources"] = [{"type": d[0], "name": d[1]} for d in data_sources]
        
        # Find providers
        providers = re.findall(r'provider\s+"([^"]+)"', content)
        metadata["providers"] = providers
        
        # Find locals
        has_locals = bool(re.search(r'locals\s*\{', content))
        metadata["has_locals"] = has_locals
        
        return metadata
    
    def _extract_js_metadata(self, content: str) -> Dict:
        """Extract JavaScript/TypeScript metadata."""
        metadata = {}
        
        # Find imports
        imports = re.findall(r"import\s+.*?from\s+['\"]([^'\"]+)['\"]", content)
        requires = re.findall(r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)", content)
        metadata["imports"] = list(set(imports + requires))[:20]
        
        # Find exports
        exports = re.findall(
            r"export\s+(?:default\s+)?(?:function|class|const|let|interface|type|enum)\s+(\w+)",
            content
        )
        metadata["exports"] = exports
        
        # Find interfaces (TypeScript)
        interfaces = re.findall(r'interface\s+(\w+)', content)
        metadata["interfaces"] = interfaces
        
        # Find types (TypeScript)
        types = re.findall(r'type\s+(\w+)\s*=', content)
        metadata["types"] = types
        
        # Check if React component
        if any(x in content for x in ["import React", "from 'react'", 'from "react"', "useState", "useEffect"]):
            metadata["is_react"] = True
        
        # Check if it's a test file
        if any(x in content for x in [".test.", ".spec.", "describe(", "it(", "test("]):
            metadata["is_test"] = True
        
        return metadata
    
    def _extract_markdown_metadata(self, content: str) -> Dict:
        """Extract Markdown metadata."""
        metadata = {}
        
        # Find title (first H1)
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if title_match:
            metadata["title"] = title_match.group(1)
        
        # Find all headings
        headings = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
        metadata["headings"] = [{"level": len(h[0]), "text": h[1]} for h in headings[:15]]
        
        # Check for code blocks
        code_blocks = re.findall(r'```(\w*)', content)
        metadata["code_languages"] = list(set(filter(None, code_blocks)))
        
        # Check for frontmatter (YAML at start)
        if content.startswith('---'):
            metadata["has_frontmatter"] = True
        
        # Check for links
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        metadata["link_count"] = len(links)
        
        return metadata
    
    def _extract_yaml_metadata(self, content: str) -> Dict:
        """Extract YAML metadata."""
        metadata = {}
        
        # Check for common YAML types
        if "apiVersion:" in content and "kind:" in content:
            metadata["is_kubernetes"] = True
            # Extract kind
            kind_match = re.search(r'kind:\s*(\w+)', content)
            if kind_match:
                metadata["k8s_kind"] = kind_match.group(1)
        
        if "AWSTemplateFormatVersion" in content or "Resources:" in content:
            metadata["is_cloudformation"] = True
        
        if "stages:" in content or "jobs:" in content:
            metadata["is_ci_config"] = True
        
        # Find top-level keys
        top_keys = re.findall(r'^(\w+):', content, re.MULTILINE)
        metadata["top_level_keys"] = list(set(top_keys))[:10]
        
        return metadata
    
    def _extract_go_metadata(self, content: str) -> Dict:
        """Extract Go metadata."""
        metadata = {}
        
        # Find package
        pkg_match = re.search(r'^package\s+(\w+)', content, re.MULTILINE)
        if pkg_match:
            metadata["package"] = pkg_match.group(1)
        
        # Find imports
        imports = re.findall(r'"([^"]+)"', content)
        metadata["imports"] = [i for i in imports if '/' in i or i in ['fmt', 'os', 'io']][:20]
        
        # Find functions
        functions = re.findall(r'^func\s+(?:\([^)]+\)\s+)?(\w+)', content, re.MULTILINE)
        metadata["functions"] = functions
        
        # Find types
        types = re.findall(r'^type\s+(\w+)\s+(?:struct|interface)', content, re.MULTILINE)
        metadata["types"] = types
        
        return metadata
    
    def _extract_rust_metadata(self, content: str) -> Dict:
        """Extract Rust metadata."""
        metadata = {}
        
        # Find uses
        uses = re.findall(r'^use\s+([\w:]+)', content, re.MULTILINE)
        metadata["uses"] = uses[:20]
        
        # Find functions
        functions = re.findall(r'^(?:pub\s+)?(?:async\s+)?fn\s+(\w+)', content, re.MULTILINE)
        metadata["functions"] = functions
        
        # Find structs
        structs = re.findall(r'^(?:pub\s+)?struct\s+(\w+)', content, re.MULTILINE)
        metadata["structs"] = structs
        
        # Find impls
        impls = re.findall(r'^impl(?:<[^>]+>)?\s+(\w+)', content, re.MULTILINE)
        metadata["impls"] = impls
        
        # Find mods
        mods = re.findall(r'^(?:pub\s+)?mod\s+(\w+)', content, re.MULTILINE)
        metadata["modules"] = mods
        
        return metadata
    
    def get_stats(self, files: List[LoadedFile]) -> Dict[str, Any]:
        """Get statistics about loaded files."""
        stats = {
            "total_files": len(files),
            "total_size_bytes": sum(f.size_bytes for f in files),
            "by_type": {},
            "by_extension": {},
        }
        
        for file in files:
            # Count by type
            type_name = file.file_type.value
            stats["by_type"][type_name] = stats["by_type"].get(type_name, 0) + 1
            
            # Count by extension
            ext = file.extension
            stats["by_extension"][ext] = stats["by_extension"].get(ext, 0) + 1
        
        return stats

