from langchain_mistralai import ChatMistralAI
from .model_provider import ModelProvider

class MistralProvider(ModelProvider):
    def __init__(self, model_id="mistral-small-latest", api_key=None, temperature=0.4):
        self.model_id = model_id
        self.api_key = api_key
        self.temperature = temperature
        
    def get_model(self):
        return ChatMistralAI(model=self.model_id, api_key=self.api_key, temperature=self.temperature)
