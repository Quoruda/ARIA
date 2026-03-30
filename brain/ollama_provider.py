from langchain_ollama import ChatOllama
from .model_provider import ModelProvider

class OllamaProvider(ModelProvider):
    def __init__(self, model_id="mistral-nemo:12b", temperature=0.4, host=None):
        self.model_id = model_id
        self.temperature = temperature
        self.host = host
        
    def get_model(self):
        return ChatOllama(model=self.model_id, base_url=self.host, temperature=self.temperature)
