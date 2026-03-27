from phi.agent import Agent
from phi.model.openai import OpenAIChat
# Or for Ollama (Local/Free):
# from phi.model.ollama import Ollama

class AgentBrain:
    def __init__(self, model_id="gpt-4o"):
        """
        Initializes the AI agent using Phidata.
        Generic implementation for any assistant name.
        """
        self.agent = Agent(
            model=OpenAIChat(id=model_id),
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

# EXAMPLE USAGE
if __name__ == "__main__":
    # Note: Requires OPENAI_API_KEY environment variable
    brain = AgentBrain()
    print(brain.get_response("Hello, are you ready?"))
