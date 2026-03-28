from phi.agent import Agent
from .ollama_provider import OllamaProvider

class AgentBrain:
    def __init__(self, provider=None):
        """
        Initializes the AI agent using Phidata and a provided model provider.
        """
        if provider is None:
            provider = OllamaProvider()
            
        self.agent = Agent(
            model=provider.get_model(),
            description="You are a sophisticated AI interface with a pixel-art face.",
            instructions=[
                "Provide concise and helpful responses.",
                "Your personality is sleek, efficient, and slightly futuristic.",
                "Transitions: 'thinking' (processing), 'speaking' (generating/outputting).",
                "Your role is to assist the user through this modular visual display system."
            ],
            markdown=True,
        )

    def get_response(self, user_input: str):
        """
        Sends user input to the agent and returns the response.
        """
        response = self.agent.run(user_input)
        return response.content
    
    def get_stream_response(self, user_input: str):
        """
        Yields the response chunk by chunk (streaming) from the agent.
        """
        # The stream=True parameter allows for generator-based output
        run_response = self.agent.run(user_input, stream=True)
        for chunk in run_response:
            # Depending on Phidata version, chunk may be a string or an object
            content = chunk.content if hasattr(chunk, 'content') else chunk
            if content:
                yield content

# EXAMPLE USAGE
if __name__ == "__main__":
    # Test with default provider (Ollama)
    brain = AgentBrain()
    print("--- Testing Streaming ---")
    for word in brain.get_stream_response("Hello, are you ready?"):
        print(word, end="", flush=True)
    print()
