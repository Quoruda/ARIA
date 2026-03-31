from langgraph.prebuilt import create_react_agent
from .ollama_provider import OllamaProvider
from .tools.time_tool import get_temporal_context
from .tools.trigger_tool import schedule_action

class AgentBrain:
    def __init__(self, provider=None):
        """
        Initializes the AI agent using LangGraph and a provided model provider.
        """
        if provider is None:
            provider = OllamaProvider()

        self.provider = provider

        self.system_message = (
            "You are ARIA, a sophisticated AI interface with a pixel-art face.\n"
            "Provide concise and helpful responses.\n"
            "Your personality is sleek, efficient, and slightly futuristic.\n"
            "Respond ONLY with direct spoken text. DO NOT use markers like 'Thinking...', 'Speaking:', '>', '💭', or descriptions between asterisks.\n"
            "Use 'schedule_action' for future reminders or tasks. Format: '+10m', '+1h', or 'HH:MM'.\n"
            "IMPORTANT: If the user asks for a reminder, clearly specify it in the action_prompt in the user's language (e.g., 'Rappelle à l'utilisateur de...'). Do not use raw actions like 'acheter du lait' for reminders."
        )

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
            prompt=self.system_message
        )

    def get_response(self, user_input: str):
        """
        Sends user input to the agent and returns the response.
        """
        inputs = {"messages": [("user", user_input)]}
        response = self.agent.invoke(inputs)
        return response["messages"][-1].content
    
    def get_stream_response(self, user_input: str):
        """
        Yields the response chunk by chunk (streaming) from the agent.
        Normal user prompt.
        """
        inputs = {"messages": [("user", user_input)]}
        for event in self.agent.stream(inputs, stream_mode="messages"):
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
