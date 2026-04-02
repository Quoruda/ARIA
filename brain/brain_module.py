from langgraph.prebuilt import create_react_agent
from langchain_core.messages import trim_messages, SystemMessage
from memory.context_provider import get_context_checkpointer
from .ollama_provider import OllamaProvider
from .mistral_provider import MistralProvider


class AgentBrain:
    """
    Generic base class for a LangGraph react agent.

    Subclasses define their own system prompt, tools, and memory settings
    by calling super().__init__() with the appropriate arguments.
    """

    def get_system_prompt(self) -> str:
        """
        Returns the system prompt content. 
        Subclasses should override this to provide dynamic content.
        """
        return self.system_prompt

    def __init__(
        self,
        provider=None,
        system_prompt: str = "",
        tools: list = None,
        use_memory: bool = False,
        thread_id: str = "default",
        max_messages: int = 20,
    ):
        if provider is None:
            provider = OllamaProvider()

        self.provider = provider
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.use_memory = use_memory
        self.thread_id = thread_id
        self.max_messages = max_messages

        checkpointer = get_context_checkpointer() if use_memory else None

        def _prompt_modifier(state):
            """Prepends the dynamic system message and trims history."""
            content = self.get_system_prompt()
            
            trimmed = trim_messages(
                state["messages"],
                strategy="last",
                token_counter=len,
                max_tokens=self.max_messages,
                start_on="human",
                include_system=False,
            )
            return [SystemMessage(content=content)] + trimmed

        self._agent = create_react_agent(
            provider.get_model(),
            tools=self.tools,
            prompt=_prompt_modifier,
            checkpointer=checkpointer,
        )

    # ------------------------------------------------------------------ #
    # Shared helpers                                                       #
    # ------------------------------------------------------------------ #

    @staticmethod
    def build_provider(source: str, temperature: float):
        """Instantiates the right ModelProvider from a source string."""
        import os
        if source == "mistral":
            return MistralProvider(
                model_id=os.getenv("AI_MODEL_ID", "mistral-small-latest"),
                api_key=os.getenv("MISTRAL_API_KEY"),
                temperature=temperature,
            )
        return OllamaProvider(
            model_id=os.getenv("AI_MODEL_ID", "mistral-nemo:12b"),
            host=os.getenv("OLLAMA_HOST"),
            temperature=temperature,
        )

    # ------------------------------------------------------------------ #
    # Public interface                                                     #
    # ------------------------------------------------------------------ #

    def _make_config(self) -> dict:
        return {"configurable": {"thread_id": self.thread_id}} if self.use_memory else {}

    def get_response(self, user_input: str) -> str:
        """Invokes the agent and returns the final response as a string."""
        inputs = {"messages": [("user", user_input)]}
        response = self._agent.invoke(inputs, config=self._make_config())
        return response["messages"][-1].content

    def stream(self, user_input: str):
        """Yields response chunks from the agent (streaming)."""
        inputs = {"messages": [("user", user_input)]}
        for event in self._agent.stream(inputs, stream_mode="messages", config=self._make_config()):
            message, metadata = event
            if message.content and metadata.get("langgraph_node") == "agent":
                yield message.content
