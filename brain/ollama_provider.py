from phi.model.ollama import Ollama
from .model_provider import ModelProvider

class OllamaProvider(ModelProvider):
    def __init__(self, model_id="mistral-nemo:12b", temperature=0.4, host=None):
        self.model_id = model_id
        self.temperature = temperature
        self.host = host
        
    def get_model(self):
        return Ollama(id=self.model_id, host=self.host, options={"temperature": self.temperature})
