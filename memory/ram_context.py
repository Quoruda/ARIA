from langgraph.checkpoint.memory import MemorySaver

def get_ram_context_checkpointer() -> MemorySaver:
    """Returns a volatile, RAM-based checkpointer for the conversation context."""
    return MemorySaver()
