from dataclasses import dataclass
from typing import Optional, Any

@dataclass
class MessageContext:
    """Represents a message flowing through the ARIA system."""
    
    # Identifier for the channel that emitted this message (e.g. "telegram", "local_audio")
    source_channel: str
    
    # The textual content of the message
    content: str
    
    # Identifier for the target channel that should receive the reply.
    # Typically identical to source_channel, but can be forced (e.g., in a trigger).
    target_channel: Optional[str] = None
    
    # Optional identifier for multi-user context (e.g., Telegram user_id)
    user_id: Optional[str] = None
    
    # Optional payload (like raw audio bytes, images) if needed by specific channels
    payload: Any = None

    def __post_init__(self):
        if self.target_channel is None:
            self.target_channel = self.source_channel
