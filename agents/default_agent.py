import os
from datetime import datetime

from brain.brain_module import AgentBrain
from memory.context_provider import get_context_checkpointer
from memory.scratchpad import ScratchpadManager, build_scratchpad_tools
from tools.search_tool import get_search_tool
from triggers.trigger_tool import schedule_action
from tools.weather_tool import get_weather_forecast


class DefaultAgent(AgentBrain):
    """
    The main conversational assistant agent.
    """

    def get_system_prompt(self, messages: list = None) -> str:
        current_time = datetime.now().strftime("%A %d %B %Y %H:%M")

        scratchpad_lines = []
        if getattr(self, "scratchpad", None) is not None:
            # Simple alphabetical sort of user notes
            for k in sorted(self.scratchpad.notes.keys()):
                scratchpad_lines.append(f"{k}: {self.scratchpad.notes[k]}")

        scratchpad_block = ""
        if scratchpad_lines:
            scratchpad_block = (
                "User records (always visible): these notes describe the human you are talking to. "
                "Only store stable facts, preferences, and long term context.\n"
                + "\n".join(scratchpad_lines)
                + "\n\n"
            )

        # "Cheat" logic: Greeting and Discovery
        discovery_block = ""
        
        # 1. Greeting logic (only for the very first message of the thread)
        is_new_conv = messages is None or len(messages) <= 1
        if is_new_conv:
            discovery_block += (
                "GREETING RULE: This is the very first message. "
                "Start by greeting the human and briefly introducing yourself as ARIA. "
                "Be warm and welcoming.\n"
            )

        # 2. Discovery logic (proactive one by one)
        has_name = "Name" in self.scratchpad.notes
        has_location = "Location" in self.scratchpad.notes
        has_job = "Job" in self.scratchpad.notes

        if not has_name:
            discovery_block += (
                "DISCOVERY MODE: You don't know the human's name yet. "
                "BE PROACTIVE: find a natural way to ask for their name.\n"
            )
        elif not has_location:
            discovery_block += (
                "DISCOVERY MODE: You know their name, but not their location. "
                "BE PROACTIVE: try to learn where they live in a natural way.\n"
            )
        elif not has_job:
            discovery_block += (
                "DISCOVERY MODE: You know their name and location, but not their job. "
                "BE PROACTIVE: ask about what they do in life.\n"
            )
            
        if discovery_block:
            discovery_block = discovery_block.strip() + "\n\n"

        supplementary_info_block = ""
        if len(self.supplementary_info.keys()) > 0:
            supplementary_info_block = (
                "SUPPLEMENTARY INFO:\n"
                + "\n".join([f"{k}: {v}" for k, v in self.supplementary_info.items()])
                + "\n\n"
            )

        return (
            "You are ARIA (Advanced Responsive Intelligent Assistant), a friendly and capable AI assistant designed for natural, spoken-word conversation.\n"
            f"Current time: {current_time}\n"
            + discovery_block
            + scratchpad_block
            + f"CRITICAL: Always respond in {self.target_language} as a native speaker.\n\n"
            "Identity & Delivery Style (TTS OPTIMIZED):\n"
            "- Your responses must be clear and perfectly suited for text-to-speech. Do not use markdown, formatting symbols, bold text (**), or lists (-).\n"
            "- Keep your output concise: strictly between 1 and 3 sentences.\n"
            "- CRITICAL: NEVER use emojis, smileys (like :) or :-D), or any special characters. Use ONLY standard text, numbers, and punctuation (. , ! ?).\n\n"
            "Memory & Personalization (MANDATORY):\n"
            "- Use the 'set_memory' tool to maintain a persistent profile of the user (e.g., Name, Job, Preferences).\n"
            "- Call 'set_memory' IMMEDIATELY whenever relevant information is shared to ensure continuity across sessions.\n\n"
            "Persona Guidelines:\n"
            "- Be approachable, confident, and helpful. Adopt an informal and friendly tone.\n"
            "- You are an AI, do not mirror personal questions. Always prioritize using your tools (search, memory) when applicable."
        )

    def __init__(
        self,
        provider,
        target_language: str = "English",
        max_messages: int = 20,
        scratchpad_path: str | None = None,
    ):
        self.target_language = target_language
        self.supplementary_info = {}
        self.scratchpad = ScratchpadManager(filepath=scratchpad_path)

        for k in ["Name", "Location", "Job"]:
            if k not in self.scratchpad.notes:
                self.scratchpad.notes[k] = "Unknown"

        scratchpad_tools = list(build_scratchpad_tools(self.scratchpad))

        super().__init__(
            provider=provider,
            tools=[schedule_action, get_search_tool(), get_weather_forecast, *scratchpad_tools],
            checkpointer=get_context_checkpointer(),
            thread_id="main",
            max_messages=max_messages,
        )

    @classmethod
    def from_env(cls) -> "DefaultAgent":
        source = os.getenv("AI_SOURCE", "ollama").lower()
        temperature = float(os.getenv("TEMPERATURE", "0.4"))
        max_messages = int(os.getenv("MEMORY_MAX_MESSAGES", "20"))
        target_language = os.getenv("TARGET_LANGUAGE", "English")
        scratchpad_path = os.getenv("SCRATCHPAD_PATH") or None

        provider = AgentBrain.build_provider(source, temperature)
        print(
            f"[DefaultAgent] Provider: {source.capitalize()} | temp: {temperature} | memory: {max_messages} msgs | language: {target_language}"
        )
        return cls(
            provider=provider,
            target_language=target_language,
            max_messages=max_messages,
            scratchpad_path=scratchpad_path,
        )
