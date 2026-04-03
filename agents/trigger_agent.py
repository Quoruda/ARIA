import os
from tools.time_tool import get_temporal_context
from triggers.trigger_tool import schedule_action
from brain.brain_module import AgentBrain


class TriggerAgent(AgentBrain):
    """
    A stateless, single-shot agent for executing scheduled triggers.
    """

    def get_system_prompt(self) -> str:
        return (
            "You are ARIA, a sophisticated AI interface with a pixel-art face.\n"
            "Provide concise and helpful responses.\n"
            "Your personality is sleek, efficient, and slightly futuristic.\n"
            "Respond ONLY with direct spoken text. DO NOT use markers like 'Thinking...', "
            "'Speaking:', '>', '💭', or descriptions between asterisks.\n"
            f"\nCRITICAL: You must ALWAYS respond in {self.target_language}, regardless of the language the user speaks.\n"
            "\nIMPORTANT: This is a TRIGGER EXECUTION. "
            "You are being invoked automatically to execute a scheduled task or reminder.\n"
            "If the prompt asks to remind the user, address the user naturally and explicitly "
            "deliver the reminder (e.g., 'C'est l'heure de...' or 'Je te rappelle de...').\n"
            "Do not be overly robotic or brief. "
            "Speak directly and cleanly without reformulating the core instruction or creating new tasks."
        )

    def __init__(self, provider, target_language: str = "English"):
        self.target_language = target_language
        super().__init__(
            provider=provider,
            tools=[get_temporal_context, schedule_action],
            use_memory=False,
        )

    @classmethod
    def from_env(cls) -> "TriggerAgent":
        source = os.getenv("AI_SOURCE", "ollama").lower()
        temperature = float(os.getenv("TEMPERATURE", "0.4"))
        target_language = os.getenv("TARGET_LANGUAGE", "French")

        provider = AgentBrain.build_provider(source, temperature)
        print(f"[TriggerAgent] Provider: {source.capitalize()} | temp: {temperature} | language: {target_language}")
        return cls(provider=provider, target_language=target_language)
