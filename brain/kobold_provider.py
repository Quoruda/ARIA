from langchain_openai import ChatOpenAI
from .model_provider import ModelProvider

class KoboldProvider(ModelProvider):
    """
    Provider for KoboldCPP using its OpenAI-compatible API.
    """
    def __init__(self, model_id="local-model", url="http://localhost:5001/v1", temperature=0.4):
        self.model_id = model_id
        self.url = url
        self.temperature = temperature
        
    def get_model(self):
        return ChatOpenAI(
            openai_api_base=self.url,
            openai_api_key="not-needed", 
            model_name=self.model_id,
            temperature=self.temperature
        )
