import os
from datetime import datetime
from tools.search_tool import search_tool
from tools.trigger_tool import schedule_action
from brain.brain_module import AgentBrain

_SYSTEM_PROMPT = (
    "You are ARIA, a sophisticated AI interface with a pixel-art face.\n"
    "Provide concise and helpful responses.\n"
    "Your personality is sleek, efficient, and slightly futuristic.\n"
    "Respond ONLY with direct spoken text. DO NOT use markers like 'Thinking...', "
    "'Speaking:', '>', '💭', or descriptions between asterisks.\n"
    "Use 'schedule_action' for future reminders or tasks. "
    "Format: '+10m', '+1h', or 'HH:MM'.\n"
    "IMPORTANT: If the user asks for a reminder, clearly specify it in the "
    "action_prompt in the user's language (e.g., 'Rappelle à l'utilisateur de...'). "
    "Do not use raw actions like 'acheter du lait' for reminders."
)


class DefaultAgent(AgentBrain):
    """
    The main conversational assistant agent.
    """

    def get_system_prompt(self) -> str:
        current_time = datetime.now().strftime("%A %d %B %Y %H:%M")
        return (
            "You are ARIA, a sophisticated AI interface with a pixel-art face.\n"
            f"Current time: {current_time}\n"
            "Provide concise and helpful responses.\n"
            "Your personality is sleek, efficient, and slightly futuristic.\n"
            "Respond ONLY with direct spoken text. DO NOT use markers like 'Thinking...', "
            "'Speaking:', '>', '💭', or descriptions between asterisks.\n"
            "Use 'schedule_action' for future reminders or tasks. "
            "Format: '+10m', '+1h', or 'HH:MM'.\n"
            "IMPORTANT: If the user asks for a reminder, clearly specify it in the "
            "action_prompt in the user's language (e.g., 'Rappelle à l'utilisateur de...'). "
            "Do not use raw actions like 'acheter du lait' for reminders."
        )

    def __init__(self, provider, max_messages: int = 20):
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

        provider = AgentBrain.build_provider(source, temperature)
        print(f"[DefaultAgent] Provider: {source.capitalize()} | temp: {temperature} | memory: {max_messages} msgs")
        return cls(provider=provider, max_messages=max_messages)
