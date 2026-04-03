import os
import sqlite3
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver


def get_sqlite_context_checkpointer(db_path: str = "data/context.db") -> SqliteSaver:
    """Returns a persistent, SQLite-based checkpointer for the conversation context.

    The connection is established with check_same_thread=False to allow usage across
    different threads.
    """
    parent = os.path.dirname(db_path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    # We create the connection manually because from_conn_string returns a context manager,
    # which is not directly compatible with how AgentBrain is initialized.
    conn = sqlite3.connect(db_path, check_same_thread=False)
    return SqliteSaver(conn)


def get_ram_context_checkpointer() -> MemorySaver:
    """Returns a volatile, RAM-based checkpointer for the conversation context."""
    return MemorySaver()


def get_context_checkpointer():
    """Factory: selects and returns a LangGraph checkpointer based on CONTEXT_BACKEND.

    Default: 'ram' (volatile)
    """
    backend = os.getenv("CONTEXT_BACKEND", "ram").lower()

    if backend == "sqlite":
        db_path = os.getenv("CONTEXT_DB_PATH", "data/context.db")
        return get_sqlite_context_checkpointer(db_path)

    # Fallback to RAM
    return get_ram_context_checkpointer()
