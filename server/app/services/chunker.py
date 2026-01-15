"""
Chunker - Smart chunking by file type
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from app.services.loader import LoadedFile, FileType


@dataclass
class Chunk:
    """A chunk of code/text ready for embedding"""
    content: str
    chunk_type: str  # e.g., "function", "class", "resource", "section"
    source_file: str
    file_type: FileType
    start_line: int
    end_line: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def id(self) -> str:
        """Generate a unique ID for this chunk."""
        return f"{self.source_file}:{self.start_line}-{self.end_line}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "content": self.content,
            "chunk_type": self.chunk_type,
            "source_file": self.source_file,
            "file_type": self.file_type.value,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "metadata": self.metadata,
        }


class Chunker:
    """
    Smart chunker that splits files based on their type.
    Uses semantic boundaries (functions, classes, blocks) rather than
    arbitrary character counts.
    """
    
    def __init__(
        self,
        default_chunk_size: int = 1500,
        chunk_overlap: int = 200,
        min_chunk_size: int = 50
    ):
        self.default_chunk_size = default_chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
    
    def chunk_file(self, file: LoadedFile) -> List[Chunk]:
        """
        Chunk a file based on its type.
        
        Args:
            file: LoadedFile to chunk
            
        Returns:
            List of Chunk objects
        """
        if file.file_type == FileType.PYTHON:
            return self._chunk_python(file)
        elif file.file_type == FileType.TERRAFORM:
            return self._chunk_terraform(file)
        elif file.file_type == FileType.MARKDOWN:
            return self._chunk_markdown(file)
        elif file.file_type in [FileType.TYPESCRIPT, FileType.JAVASCRIPT]:
            return self._chunk_javascript(file)
        elif file.file_type == FileType.GO:
            return self._chunk_go(file)
        elif file.file_type == FileType.RUST:
            return self._chunk_rust(file)
        elif file.file_type == FileType.YAML:
            return self._chunk_yaml(file)
        else:
            return self._chunk_default(file)
    
    def chunk_files(self, files: List[LoadedFile]) -> List[Chunk]:
        """
        Chunk multiple files.
        
        Args:
            files: List of LoadedFile objects
            
        Returns:
            List of all chunks from all files
        """
        all_chunks = []
        for file in files:
            chunks = self.chunk_file(file)
            all_chunks.extend(chunks)
        return all_chunks
    
    # =========================================================================
    # Python Chunking
    # =========================================================================
    
    def _chunk_python(self, file: LoadedFile) -> List[Chunk]:
        """Chunk Python by functions and classes."""
        chunks = []
        content = file.content
        lines = content.split('\n')
        
        # Pattern for class and function definitions at various indentation levels
        # We focus on top-level and class-level definitions
        pattern = r'^(class\s+\w+|(?:async\s+)?def\s+\w+)'
        
        current_start = 0
        current_type = "module_header"
        
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            indent = len(line) - len(stripped)
            
            # Only chunk on top-level definitions (no indent) or single indent (class methods)
            if indent <= 4 and re.match(pattern, stripped):
                # Save previous chunk if substantial
                if i > current_start:
                    chunk_content = '\n'.join(lines[current_start:i])
                    if len(chunk_content.strip()) >= self.min_chunk_size:
                        chunks.append(self._create_chunk(
                            content=chunk_content,
                            chunk_type=current_type,
                            file=file,
                            start_line=current_start + 1,
                            end_line=i
                        ))
                
                current_start = i
                if stripped.startswith("class"):
                    current_type = "class"
                else:
                    current_type = "function"
        
        # Don't forget the last chunk
        if current_start < len(lines):
            chunk_content = '\n'.join(lines[current_start:])
            if len(chunk_content.strip()) >= self.min_chunk_size:
                chunks.append(self._create_chunk(
                    content=chunk_content,
                    chunk_type=current_type,
                    file=file,
                    start_line=current_start + 1,
                    end_line=len(lines)
                ))
        
        # If no semantic chunks found, fall back to default
        return chunks if chunks else self._chunk_default(file)
    
    # =========================================================================
    # Terraform Chunking
    # =========================================================================
    
    def _chunk_terraform(self, file: LoadedFile) -> List[Chunk]:
        """Chunk Terraform by resource/module blocks."""
        chunks = []
        content = file.content
        
        # Pattern for Terraform blocks
        block_pattern = r'(resource|data|module|variable|output|locals|terraform|provider)\s+"?([^"\s{]+)"?\s*(?:"([^"]+)")?\s*\{'
        
        # Find all block starts
        matches = list(re.finditer(block_pattern, content))
        
        if not matches:
            return self._chunk_default(file)
        
        for i, match in enumerate(matches):
            start = match.start()
            
            # Find the end of this block (matching braces)
            end = self._find_block_end(content, match.end() - 1)
            
            block_content = content[start:end]
            block_type = match.group(1)
            resource_type = match.group(2)
            resource_name = match.group(3) or resource_type
            
            # Calculate line numbers
            start_line = content[:start].count('\n') + 1
            end_line = content[:end].count('\n') + 1
            
            chunk_metadata = {
                **file.metadata,
                "block_type": block_type,
                "resource_type": resource_type,
                "resource_name": resource_name,
                "terraform_id": f"{resource_type}.{resource_name}" if block_type == "resource" else resource_name,
            }
            
            chunks.append(Chunk(
                content=block_content,
                chunk_type=f"terraform_{block_type}",
                source_file=file.relative_path,
                file_type=file.file_type,
                start_line=start_line,
                end_line=end_line,
                metadata=chunk_metadata
            ))
        
        return chunks
    
    # =========================================================================
    # Markdown Chunking
    # =========================================================================
    
    def _chunk_markdown(self, file: LoadedFile) -> List[Chunk]:
        """Chunk Markdown by sections (headings)."""
        chunks = []
        content = file.content
        lines = content.split('\n')
        
        current_start = 0
        current_heading = "Introduction"
        current_level = 0
        
        for i, line in enumerate(lines):
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            
            if heading_match:
                # Save previous section
                if i > current_start:
                    chunk_content = '\n'.join(lines[current_start:i])
                    if len(chunk_content.strip()) >= self.min_chunk_size:
                        chunks.append(self._create_chunk(
                            content=chunk_content,
                            chunk_type="markdown_section",
                            file=file,
                            start_line=current_start + 1,
                            end_line=i,
                            extra_metadata={
                                "heading": current_heading,
                                "heading_level": current_level,
                            }
                        ))
                
                current_start = i
                current_heading = heading_match.group(2)
                current_level = len(heading_match.group(1))
        
        # Last section
        if current_start < len(lines):
            chunk_content = '\n'.join(lines[current_start:])
            if len(chunk_content.strip()) >= self.min_chunk_size:
                chunks.append(self._create_chunk(
                    content=chunk_content,
                    chunk_type="markdown_section",
                    file=file,
                    start_line=current_start + 1,
                    end_line=len(lines),
                    extra_metadata={
                        "heading": current_heading,
                        "heading_level": current_level,
                    }
                ))
        
        return chunks if chunks else self._chunk_default(file)
    
    # =========================================================================
    # JavaScript/TypeScript Chunking
    # =========================================================================
    
    def _chunk_javascript(self, file: LoadedFile) -> List[Chunk]:
        """Chunk JS/TS by exports, functions, and classes."""
        chunks = []
        content = file.content
        lines = content.split('\n')
        
        # Pattern for exports, functions, classes, interfaces
        pattern = r'^(export\s+(?:default\s+)?(?:async\s+)?(?:function|class|const|let|interface|type|enum)|(?:async\s+)?function\s+\w+|class\s+\w+|interface\s+\w+)'
        
        current_start = 0
        current_type = "imports"
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if re.match(pattern, stripped):
                if i > current_start:
                    chunk_content = '\n'.join(lines[current_start:i])
                    if len(chunk_content.strip()) >= self.min_chunk_size:
                        chunks.append(self._create_chunk(
                            content=chunk_content,
                            chunk_type=current_type,
                            file=file,
                            start_line=current_start + 1,
                            end_line=i
                        ))
                
                current_start = i
                if "class" in stripped:
                    current_type = "class"
                elif "interface" in stripped:
                    current_type = "interface"
                elif "function" in stripped:
                    current_type = "function"
                elif "type" in stripped:
                    current_type = "type"
                else:
                    current_type = "export"
        
        # Last chunk
        if current_start < len(lines):
            chunk_content = '\n'.join(lines[current_start:])
            if len(chunk_content.strip()) >= self.min_chunk_size:
                chunks.append(self._create_chunk(
                    content=chunk_content,
                    chunk_type=current_type,
                    file=file,
                    start_line=current_start + 1,
                    end_line=len(lines)
                ))
        
        return chunks if chunks else self._chunk_default(file)
    
    # =========================================================================
    # Go Chunking
    # =========================================================================
    
    def _chunk_go(self, file: LoadedFile) -> List[Chunk]:
        """Chunk Go by functions and types."""
        chunks = []
        content = file.content
        lines = content.split('\n')
        
        # Pattern for Go definitions
        pattern = r'^(func\s+(?:\([^)]+\)\s+)?\w+|type\s+\w+\s+(?:struct|interface))'
        
        current_start = 0
        current_type = "package_header"
        
        for i, line in enumerate(lines):
            if re.match(pattern, line):
                if i > current_start:
                    chunk_content = '\n'.join(lines[current_start:i])
                    if len(chunk_content.strip()) >= self.min_chunk_size:
                        chunks.append(self._create_chunk(
                            content=chunk_content,
                            chunk_type=current_type,
                            file=file,
                            start_line=current_start + 1,
                            end_line=i
                        ))
                
                current_start = i
                if line.startswith("func"):
                    current_type = "function"
                else:
                    current_type = "type"
        
        # Last chunk
        if current_start < len(lines):
            chunk_content = '\n'.join(lines[current_start:])
            if len(chunk_content.strip()) >= self.min_chunk_size:
                chunks.append(self._create_chunk(
                    content=chunk_content,
                    chunk_type=current_type,
                    file=file,
                    start_line=current_start + 1,
                    end_line=len(lines)
                ))
        
        return chunks if chunks else self._chunk_default(file)
    
    # =========================================================================
    # Rust Chunking
    # =========================================================================
    
    def _chunk_rust(self, file: LoadedFile) -> List[Chunk]:
        """Chunk Rust by functions, impls, and structs."""
        chunks = []
        content = file.content
        lines = content.split('\n')
        
        # Pattern for Rust definitions
        pattern = r'^(?:pub\s+)?(?:async\s+)?(?:fn|struct|enum|impl|trait|mod)\s+'
        
        current_start = 0
        current_type = "module_header"
        
        for i, line in enumerate(lines):
            if re.match(pattern, line):
                if i > current_start:
                    chunk_content = '\n'.join(lines[current_start:i])
                    if len(chunk_content.strip()) >= self.min_chunk_size:
                        chunks.append(self._create_chunk(
                            content=chunk_content,
                            chunk_type=current_type,
                            file=file,
                            start_line=current_start + 1,
                            end_line=i
                        ))
                
                current_start = i
                if "fn " in line:
                    current_type = "function"
                elif "struct " in line:
                    current_type = "struct"
                elif "impl " in line:
                    current_type = "impl"
                elif "trait " in line:
                    current_type = "trait"
                elif "enum " in line:
                    current_type = "enum"
                elif "mod " in line:
                    current_type = "module"
        
        # Last chunk
        if current_start < len(lines):
            chunk_content = '\n'.join(lines[current_start:])
            if len(chunk_content.strip()) >= self.min_chunk_size:
                chunks.append(self._create_chunk(
                    content=chunk_content,
                    chunk_type=current_type,
                    file=file,
                    start_line=current_start + 1,
                    end_line=len(lines)
                ))
        
        return chunks if chunks else self._chunk_default(file)
    
    # =========================================================================
    # YAML Chunking
    # =========================================================================
    
    def _chunk_yaml(self, file: LoadedFile) -> List[Chunk]:
        """Chunk YAML by top-level keys."""
        chunks = []
        content = file.content
        lines = content.split('\n')
        
        current_start = 0
        current_key = "header"
        
        for i, line in enumerate(lines):
            # Top-level key (no indentation, ends with :)
            if line and not line[0].isspace() and ':' in line:
                if i > current_start:
                    chunk_content = '\n'.join(lines[current_start:i])
                    if len(chunk_content.strip()) >= self.min_chunk_size:
                        chunks.append(self._create_chunk(
                            content=chunk_content,
                            chunk_type="yaml_section",
                            file=file,
                            start_line=current_start + 1,
                            end_line=i,
                            extra_metadata={"yaml_key": current_key}
                        ))
                
                current_start = i
                current_key = line.split(':')[0].strip()
        
        # Last chunk
        if current_start < len(lines):
            chunk_content = '\n'.join(lines[current_start:])
            if len(chunk_content.strip()) >= self.min_chunk_size:
                chunks.append(self._create_chunk(
                    content=chunk_content,
                    chunk_type="yaml_section",
                    file=file,
                    start_line=current_start + 1,
                    end_line=len(lines),
                    extra_metadata={"yaml_key": current_key}
                ))
        
        return chunks if chunks else self._chunk_default(file)
    
    # =========================================================================
    # Default Chunking
    # =========================================================================
    
    def _chunk_default(self, file: LoadedFile) -> List[Chunk]:
        """Default chunking by character count with overlap."""
        chunks = []
        content = file.content
        
        # If file is small enough, return as single chunk
        if len(content) <= self.default_chunk_size:
            return [Chunk(
                content=content,
                chunk_type="file",
                source_file=file.relative_path,
                file_type=file.file_type,
                start_line=1,
                end_line=content.count('\n') + 1,
                metadata=file.metadata
            )]
        
        # Split by paragraphs/sections
        start = 0
        chunk_index = 0
        
        while start < len(content):
            end = min(start + self.default_chunk_size, len(content))
            
            # Try to break at a newline
            if end < len(content):
                # Look for double newline (paragraph break) first
                para_break = content.rfind('\n\n', start, end)
                if para_break > start + self.min_chunk_size:
                    end = para_break + 2
                else:
                    # Fall back to single newline
                    newline_pos = content.rfind('\n', start + self.min_chunk_size, end)
                    if newline_pos > start:
                        end = newline_pos + 1
            
            chunk_content = content[start:end]
            
            if len(chunk_content.strip()) >= self.min_chunk_size:
                chunks.append(Chunk(
                    content=chunk_content,
                    chunk_type="text_chunk",
                    source_file=file.relative_path,
                    file_type=file.file_type,
                    start_line=content[:start].count('\n') + 1,
                    end_line=content[:end].count('\n') + 1,
                    metadata={**file.metadata, "chunk_index": chunk_index}
                ))
            
            # Move start with overlap
            start = end - self.chunk_overlap if end < len(content) else end
            chunk_index += 1
        
        return chunks
    
    # =========================================================================
    # Helpers
    # =========================================================================
    
    def _create_chunk(
        self,
        content: str,
        chunk_type: str,
        file: LoadedFile,
        start_line: int,
        end_line: int,
        extra_metadata: Optional[Dict] = None
    ) -> Chunk:
        """Helper to create a chunk with merged metadata."""
        metadata = {**file.metadata}
        if extra_metadata:
            metadata.update(extra_metadata)
        
        return Chunk(
            content=content,
            chunk_type=chunk_type,
            source_file=file.relative_path,
            file_type=file.file_type,
            start_line=start_line,
            end_line=end_line,
            metadata=metadata
        )
    
    def _find_block_end(self, content: str, start: int) -> int:
        """Find the matching closing brace for Terraform/JSON blocks."""
        depth = 1
        i = start + 1
        
        while i < len(content) and depth > 0:
            char = content[i]
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
            i += 1
        
        return i
    
    def get_stats(self, chunks: List[Chunk]) -> Dict[str, Any]:
        """Get statistics about chunks."""
        stats = {
            "total_chunks": len(chunks),
            "total_characters": sum(len(c.content) for c in chunks),
            "by_type": {},
            "by_file_type": {},
            "avg_chunk_size": 0,
        }
        
        if chunks:
            stats["avg_chunk_size"] = stats["total_characters"] // len(chunks)
        
        for chunk in chunks:
            # Count by chunk type
            stats["by_type"][chunk.chunk_type] = stats["by_type"].get(chunk.chunk_type, 0) + 1
            
            # Count by file type
            ft = chunk.file_type.value
            stats["by_file_type"][ft] = stats["by_file_type"].get(ft, 0) + 1
        
        return stats

