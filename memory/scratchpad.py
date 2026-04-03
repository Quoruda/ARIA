from __future__ import annotations

import json
import os
from typing import Dict, Optional, Tuple

from langchain_core.tools import tool


class ScratchpadManager:
    def __init__(self, filepath: Optional[str] = None):
        self.filepath = filepath or None
        self.notes: Dict[str, str] = {}
        if self.filepath is not None:
            self._load()

    def _load(self) -> None:
        """Load a simple flat key:value JSON scratchpad."""
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                self.notes = {str(k): str(v) for k, v in data.items()}
            else:
                self.notes = {}
        except (FileNotFoundError, json.JSONDecodeError):
            self.notes = {}

    def _save(self) -> None:
        """Persist the notes to JSON."""
        if self.filepath is None:
            return
        try:
            parent = os.path.dirname(self.filepath)
            if parent:
                os.makedirs(parent, exist_ok=True)
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.notes, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def set_memory(self, key: str, value: str) -> None:
        """Add, update or delete a piece of user information."""
        k = str(key).strip()
        v = str(value).strip()
        
        if not k:
            raise ValueError("key cannot be empty")
            
        if not v:
            if k in self.notes:
                del self.notes[k]
        else:
            self.notes[k] = v
        self._save()


def build_scratchpad_tools(manager: ScratchpadManager) -> Tuple[object, ...]:
    @tool
    def set_memory(key: str, value: str) -> str:
        """Store or update any information about the user.
        
        Args:
            key: Descriptive key (e.g., 'Name', 'Job', 'Likes', 'Pet').
            value: The information to store. Leave empty to delete the key.
        """
        try:
            manager.set_memory(key, value)
            return f"Memory '{key}' updated successfully."
        except Exception as e:
            return f"Error: {str(e)}"

    return (set_memory,)
