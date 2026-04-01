import os
from .ram_context import get_ram_context_checkpointer

def get_context_checkpointer():
    """
    Factory: Selects and returns a LangGraph checkpointer based on MEMORY_BACKEND.
    Default: 'ram' (volatile)
    """
    # Using 'context' in environment variables as well for consistency
    backend = os.getenv("CONTEXT_BACKEND", "ram").lower()

    if backend == "sqlite":
        from .sqlite_context import get_sqlite_context_checkpointer
        db_path = os.getenv("CONTEXT_DB_PATH", "data/context.db")
        return get_sqlite_context_checkpointer(db_path)
    
    # Fallback to RAM
    return get_ram_context_checkpointer()
