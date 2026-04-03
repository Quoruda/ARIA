import os
import sqlite3
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver

def get_sqlite_context_checkpointer(db_path: str = "data/context.db") -> SqliteSaver:
    """
    Returns a persistent, SQLite-based checkpointer for the conversation context.
    The connection is established with check_same_thread=False to allow usage across different threads.
    """
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    # We create the connection manually because from_conn_string returns a context manager,
    # which is not directly compatible with how AgentBrain is initialized.
    conn = sqlite3.connect(db_path, check_same_thread=False)
    return SqliteSaver(conn)

def get_ram_context_checkpointer() -> MemorySaver:
    """Returns a volatile, RAM-based checkpointer for the conversation context."""
    return MemorySaver()


def get_context_checkpointer():
    """
    Factory: Selects and returns a LangGraph checkpointer based on MEMORY_BACKEND.
    Default: 'ram' (volatile)
    """
    # Using 'context' in environment variables as well for consistency
    backend = os.getenv("CONTEXT_BACKEND", "ram").lower()

    if backend == "sqlite":
        db_path = os.getenv("CONTEXT_DB_PATH", "data/context.db")
        return get_sqlite_context_checkpointer(db_path)
    
    # Fallback to RAM
    return get_ram_context_checkpointer()
