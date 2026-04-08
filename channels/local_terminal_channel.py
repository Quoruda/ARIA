import asyncio
import sys
from typing import AsyncGenerator, Generator
from .base import BaseChannel
from .message import MessageContext

class LocalTerminalChannel(BaseChannel):
    """A channel that interacts via text in the standard console/terminal."""
    
    def __init__(self, name: str = "local_terminal"):
        super().__init__(name)
        self._running = False
        self._task = None

    async def start(self):
        self._running = True
        sys.stdin.reconfigure(encoding='utf-8')
        print("\n💡 [Terminal] Tape ton message et appuie sur Entrée (Ctrl+C pour quitter).")
        loop = asyncio.get_running_loop()
        self._task = loop.create_task(self._input_loop())

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()

    async def _input_loop(self):
        while self._running:
            try:
                # `input` is blocking, run it in a thread to keep the asyncio loop alive
                user_text = await asyncio.to_thread(input, "\n> ")
                user_text = user_text.strip()
                if user_text and self.on_message_received:
                    msg = MessageContext(source_channel=self.name, content=user_text)
                    await self.on_message_received(msg)
            except EOFError:
                self._running = False
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Terminal Error: {e}")

    async def send_async(self, message: MessageContext):
        content = message.content
        
        # Determine if content is an iterator/generator (streamed) or a simple string
        if hasattr(content, "__aiter__"):
            print("🤖 ARIA: ", end="", flush=True)
            async for chunk in content:
                print(chunk, end="", flush=True)
            print()
        elif hasattr(content, "__iter__") and not isinstance(content, str):
            print("🤖 ARIA: ", end="", flush=True)
            for chunk in content:
                print(chunk, end="", flush=True)
            print()
        else:
            print(f"🤖 ARIA: {content}")
