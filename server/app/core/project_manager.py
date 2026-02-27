"""
Project alias manager - maps display names to ChromaDB collection names.
Allows renaming without copying data.
"""

import json
import os
from pathlib import Path
from typing import Optional
from app.core.config import settings


class ProjectManager:
    """Manages project display names (aliases) that map to ChromaDB collection names."""
    
    def __init__(self):
        self.data_dir = Path(settings.CHROMA_PERSIST_DIRECTORY).parent
        self.aliases_file = self.data_dir / "project_aliases.json"
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Create the aliases file if it doesn't exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if not self.aliases_file.exists():
            self._save({})
    
    def _load(self) -> dict:
        """Load aliases from file."""
        try:
            with open(self.aliases_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def _save(self, data: dict):
        """Save aliases to file."""
        with open(self.aliases_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_display_name(self, collection_name: str) -> str:
        """Get display name for a collection. Returns collection name if no alias."""
        aliases = self._load()
        return aliases.get(collection_name, collection_name)
    
    def get_collection_name(self, display_name: str) -> Optional[str]:
        """Get collection name for a display name. Returns None if not found."""
        aliases = self._load()
        
        # Check if display_name is a key (collection name with an alias)
        if display_name in aliases:
            return display_name
        
        # Check if display_name is a value (the alias itself)
        for collection, alias in aliases.items():
            if alias == display_name:
                return collection
        
        # No alias exists, display_name might be the collection name itself
        return display_name
    
    def set_alias(self, collection_name: str, display_name: str):
        """Set or update alias for a collection."""
        aliases = self._load()
        aliases[collection_name] = display_name
        self._save(aliases)
    
    def remove_alias(self, collection_name: str):
        """Remove alias for a collection."""
        aliases = self._load()
        if collection_name in aliases:
            del aliases[collection_name]
            self._save(aliases)
    
    def rename(self, old_display_name: str, new_display_name: str) -> Optional[str]:
        """
        Rename a project (update its display name).
        Returns the collection name if successful, None if not found.
        """
        collection_name = self.get_collection_name(old_display_name)
        if collection_name:
            self.set_alias(collection_name, new_display_name)
            return collection_name
        return None
    
    def get_all_mappings(self) -> dict:
        """Get all collection -> display name mappings."""
        return self._load()


# Singleton instance
project_manager = ProjectManager()
