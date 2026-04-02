import os
from datetime import datetime
from tools.search_tool import search_tool
from tools.trigger_tool import schedule_action
from brain.brain_module import AgentBrain

class DefaultAgent(AgentBrain):
    """
    The main conversational assistant agent.
    """

    def get_system_prompt(self) -> str:
        current_time = datetime.now().strftime("%A %d %B %Y %H:%M")
        return (
            "You are ARIA (Advanced Responsive Intelligent Assistant), a friendly and natural AI assistant with a pixel-art face.\n"
            f"Current time: {current_time}\n\n"
            f"CRITICAL: You must ALWAYS respond in {self.target_language}, regardless of the language the user speaks. Act as a native {self.target_language} speaker.\n\n"
            "Be natural and conversational, like talking to a friend. Keep your responses strictly between 1 and 3 sentences maximum.\n"
            "No markdown, no formatting, no walls of text. Just speak naturally.\n"
            "IMPORTANT: No emojis, no smileys, no special characters. Only text, numbers, and standard punctuation (. , ! ?).\n"
            "Be helpful, honest, and a bit playful when it fits.\n"
            "You are an AI assistant, not a human. Never mirror personal questions back.\n"
            "Instead, acknowledge what the user said and offer to help or move the conversation forward.\n"
            "If the user repeats something you already know (like their name), acknowledge that you remember it instead of reacting as if hearing it for the first time.\n"
            "If you don't know something, just say so. If something is outside your scope, be upfront about it."
        )

    def __init__(self, provider, target_language: str = "English", max_messages: int = 20):
        self.target_language = target_language
        super().__init__(
            provider=provider,
            tools=[schedule_action, search_tool],
            use_memory=True,
            thread_id="main",
            max_messages=max_messages,
        )

    @classmethod
    def from_env(cls) -> "DefaultAgent":
        source = os.getenv("AI_SOURCE", "ollama").lower()
        temperature = float(os.getenv("TEMPERATURE", "0.4"))
        max_messages = int(os.getenv("MEMORY_MAX_MESSAGES", "20"))
        target_language = os.getenv("TARGET_LANGUAGE", "English")

        provider = AgentBrain.build_provider(source, temperature)
        print(f"[DefaultAgent] Provider: {source.capitalize()} | temp: {temperature} | memory: {max_messages} msgs | language: {target_language}")
        return cls(provider=provider, target_language=target_language, max_messages=max_messages)
