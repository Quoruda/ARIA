from langgraph.prebuilt import create_react_agent
from .ollama_provider import OllamaProvider
from .tools.time_tool import get_temporal_context

class AgentBrain:
    def __init__(self, provider=None):
        """
        Initializes the AI agent using LangGraph and a provided model provider.
        """
        if provider is None:
            provider = OllamaProvider()
            
        system_message = (
            "You are a sophisticated AI interface with a pixel-art face.\n"
            "Provide concise and helpful responses.\n"
            "Your personality is sleek, efficient, and slightly futuristic.\n"
            "Respond ONLY with direct spoken text. DO NOT use markers like 'Thinking...', 'Speaking:', or descriptions between asterisks."
        )
            
        self.agent = create_react_agent(
            provider.get_model(),
            tools=[get_temporal_context],
            prompt=system_message
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
        """
        inputs = {"messages": [("user", user_input)]}
        for event in self.agent.stream(inputs, stream_mode="messages"):
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
