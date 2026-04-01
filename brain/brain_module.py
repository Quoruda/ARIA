from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import trim_messages, SystemMessage
from .ollama_provider import OllamaProvider
from .mistral_provider import MistralProvider
from tools.time_tool import get_temporal_context
from tools.trigger_tool import schedule_action


class AgentBrain:
    @classmethod
    def from_env(cls) -> "AgentBrain":
        """Reads AI provider configuration from environment variables and returns a ready AgentBrain."""
        import os
        source = os.getenv("AI_SOURCE", "ollama").lower()
        temperature = float(os.getenv("TEMPERATURE", "0.4"))
        max_messages = int(os.getenv("MEMORY_MAX_MESSAGES", "20"))

        if source == "mistral":
            print(f"Mode: Mistral AI API (temp: {temperature}, memory: {max_messages} msgs)")
            provider = MistralProvider(
                model_id=os.getenv("AI_MODEL_ID", "mistral-small-latest"),
                api_key=os.getenv("MISTRAL_API_KEY"),
                temperature=temperature
            )
        else:
            model_id = os.getenv("AI_MODEL_ID", "mistral-nemo:12b")
            print(f"Mode: Ollama ({model_id}, temp: {temperature}, memory: {max_messages} msgs)")
            provider = OllamaProvider(
                model_id=model_id,
                host=os.getenv("OLLAMA_HOST"),
                temperature=temperature
            )

        return cls(provider=provider, max_messages=max_messages)


    def __init__(self, provider=None, max_messages=20):
        """
        Initializes the AI agent using LangGraph and a provided model provider.
        """
        if provider is None:
            provider = OllamaProvider()

        self.provider = provider
        self.max_messages = max_messages
        self._memory = MemorySaver()

        self.system_message = (
            "You are ARIA, a sophisticated AI interface with a pixel-art face.\n"
            "Provide concise and helpful responses.\n"
            "Your personality is sleek, efficient, and slightly futuristic.\n"
            "Respond ONLY with direct spoken text. DO NOT use markers like 'Thinking...', 'Speaking:', '>', '💭', or descriptions between asterisks.\n"
            "Use 'schedule_action' for future reminders or tasks. Format: '+10m', '+1h', or 'HH:MM'.\n"
            "IMPORTANT: If the user asks for a reminder, clearly specify it in the action_prompt in the user's language (e.g., 'Rappelle à l'utilisateur de...'). Do not use raw actions like 'acheter du lait' for reminders."
        )

        # Functional prompt logic to trim messages while keeping the system prompt
        def state_modifier(state):
            messages = state["messages"]
            # We trim the history to the last N messages
            trimmed_messages = trim_messages(
                messages,
                strategy="last",
                token_counter=len, # Count by message count, not actual tokens
                max_tokens=self.max_messages,
                start_on="human",
                include_system=False, # We'll re-add ours manually
            )
            return [SystemMessage(content=self.system_message)] + trimmed_messages

        self.trigger_system_message = (
            self.system_message + "\n\n"
            "IMPORTANT: This is a TRIGGER EXECUTION. "
            "You are being invoked automatically to execute a scheduled task or reminder.\n"
            "If the prompt asks to remind the user, address the user naturally and explicitly deliver the reminder (e.g., 'C'est l'heure de...' or 'Je te rappelle de...').\n"
            "Do not be overly robotic or brief. Speak directly and cleanly without reformulating the core instruction or creating new tasks."
        )

        self.agent = create_react_agent(
            provider.get_model(),
            tools=[get_temporal_context, schedule_action],
            prompt=state_modifier,
            checkpointer=self._memory
        )

    def get_response(self, user_input: str):
        """
        Sends user input to the agent and returns the response.
        """
        inputs = {"messages": [("user", user_input)]}
        config = {"configurable": {"thread_id": "main"}}
        response = self.agent.invoke(inputs, config=config)
        return response["messages"][-1].content
    
    def get_stream_response(self, user_input: str):
        """
        Yields the response chunk by chunk (streaming) from the agent.
        Normal user prompt.
        """
        inputs = {"messages": [("user", user_input)]}
        config = {"configurable": {"thread_id": "main"}}
        for event in self.agent.stream(inputs, stream_mode="messages", config=config):
            message, metadata = event
            if message.content and metadata.get("langgraph_node") == "agent":
                yield message.content

    def get_stream_response_trigger(self, user_input: str):
        """
        Yields the response chunk by chunk (streaming) from the agent.
        Trigger execution mode - AI executes directly without reformulation.
        """
        trigger_agent = create_react_agent(
            self.provider.get_model(),
            tools=[get_temporal_context, schedule_action],
            prompt=self.trigger_system_message
        )

        inputs = {"messages": [("user", user_input)]}
        for event in trigger_agent.stream(inputs, stream_mode="messages"):
            message, metadata = event
            if message.content and metadata.get("langgraph_node") == "agent":
                yield message.content

# EXAMPLE USAGE
if __name__ == "__main__":
    # Test with default provider (Ollama)
    brain = AgentBrain()
    print("--- Testing Streaming ---")
    for word in brain.get_stream_response("Hello, are you ready?"):
        print(word, end="", flush=True)
    print()
