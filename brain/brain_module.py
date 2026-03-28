from phi.agent import Agent
from phi.model.ollama import Ollama

class AgentBrain:
    def __init__(self, model_id="mistral-nemo:12b"):
        """
        Initializes the AI agent using Phidata.
        Generic implementation for any assistant name.
        """
        self.agent = Agent(
            model=Ollama(id=model_id),
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
        # Le paramètre stream=True permet de récupérer un générateur
        run_response = self.agent.run(user_input, stream=True)
        for chunk in run_response:
            # Selon la version de Phidata, chunk peut être un string ou un objet
            content = chunk.content if hasattr(chunk, 'content') else chunk
            if content:
                yield content

# EXAMPLE USAGE
if __name__ == "__main__":
    brain = AgentBrain()
    print(brain.get_response("Hello, are you ready?"))
