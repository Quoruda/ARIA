from langgraph.prebuilt import create_react_agent
from langchain_core.messages import trim_messages, SystemMessage

from .ollama_provider import OllamaProvider
from .mistral_provider import MistralProvider
from .kobold_provider import KoboldProvider


class AgentBrain:
    """
    Generic base class for a LangGraph react agent.

    Subclasses define their own system prompt, tools, and memory settings
    by calling super().__init__() with the appropriate arguments.
    """

    def get_system_prompt(self, messages: list = None) -> str:
        """
        Returns the system prompt content.
        Subclasses should override this to provide dynamic content based on history.
        """
        return self.system_prompt

    def __init__(
        self,
        provider=None,
        system_prompt: str = "",
        tools: list = None,
        thread_id: str = "default",
        max_messages: int = 20,
        checkpointer=None,
    ):
        if provider is None:
            provider = OllamaProvider()

        self.provider = provider
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.thread_id = thread_id
        self.max_messages = max_messages
        self.checkpointer = checkpointer

        def _prompt_modifier(state):
            """Prepends the dynamic system message and trims history."""
            content = self.get_system_prompt(state.get("messages", []))

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
            checkpointer=self.checkpointer,
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
        if source == "kobold":
            return KoboldProvider(
                model_id=os.getenv("AI_MODEL_ID", "local-model"),
                url=os.getenv("KOBOLD_URL", "http://localhost:5001/v1"),
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
        if self.checkpointer is None:
            return {}
        return {"configurable": {"thread_id": self.thread_id}}

    def get_response(self, user_input: str) -> str:
        """Invokes the agent and returns the final response as a string."""
        inputs = {"messages": [("user", user_input)]}
        response = self._agent.invoke(inputs, config=self._make_config())
        return response["messages"][-1].content

    def stream(self, user_input: str):
        """Yields response chunks from the agent (streaming)."""
        inputs = {"messages": [("user", user_input)]}
        last_content = ""

        for event in self._agent.stream(inputs, config=self._make_config()):
            # event is a dict with node names as keys, extract agent responses
            if "agent" in event:
                agent_state = event["agent"]
                if isinstance(agent_state, dict) and "messages" in agent_state:
                    # Only get the LAST message (the agent's response, not history)
                    if agent_state["messages"]:
                        msg = agent_state["messages"][-1]
                        if hasattr(msg, "content") and msg.content:
                            # Only yield the NEW content that wasn't yielded before
                            if msg.content != last_content:
                                new_content = msg.content[len(last_content):]
                                if new_content:
                                    last_content = msg.content
                                    yield new_content
