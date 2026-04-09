import asyncio
from abc import ABC, abstractmethod
from typing import Callable, Awaitable, Optional
from .message import MessageContext

class BaseChannel(ABC):
    """Base interface for all input/output channels in the ARIA system."""
    
    def __init__(self, name: str):
        self.name = name
        # Orchestrator callback: async function that accepts a MessageContext
        self.on_message_received: Optional[Callable[[MessageContext], Awaitable[None]]] = None

    def set_callback(self, callback: Callable[[MessageContext], Awaitable[None]]):
        """Registers the callback the channel will fire when it receives user input."""
        self.on_message_received = callback

    async def start(self):
        """Starts the channel (listening loops, bots polling, etc.)."""
        pass

    async def stop(self):
        """Stops the channel and cleans up resources."""
        pass

    @abstractmethod
    async def send_async(self, message: MessageContext):
        """Dispatches an outgoing message to the user via this channel."""
        ...
