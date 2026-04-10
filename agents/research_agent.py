import os
from langchain_core.tools import tool, BaseTool
from brain.plan_execute_base import PlanExecuteBase
from brain.agent_base import AgentBase
from tools.search_tool import get_search_tool

class ResearchAgent(PlanExecuteBase):
    """
    An advanced agent dedicated to deep research using the Plan-and-Execute paradigm.
    """
    
    def _print_available_tools(self):
        """Display all available tools for this agent."""
        print("\n" + "="*60)
        print("🛠️  AVAILABLE TOOLS (RESEARCH AGENT)")
        print("="*60)

        if not self.tools:
            print("❌ No tools available")
        else:
            for i, tool in enumerate(self.tools, 1):
                tool_name = getattr(tool, "name", "Unknown")
                tool_description = getattr(tool, "description", "No description")
                print(f"\n{i}. {tool_name}")
                print(f"   Description: {tool_description}")

        print("="*60 + "\n")

    def __init__(self, provider, checkpointer=None, max_messages: int = 50):
        # 1. Load the required tools
        tools = []
        search = get_search_tool()
        if search:
            tools.append(search)
            
        # 2. Define its identity and rules
        system_prompt = (
            "You are an Elite Research Analyst AI.\n"
            "Your singular purpose is to investigate complex topics deeply, leaving no stone unturned.\n"
            "If the information you find is contradictory or incomplete, formulate sub-queries to resolve the ambiguity.\n"
            "Do not stop until you have a comprehensive, multi-faceted understanding of the subject.\n"
            "Always synthesize your final response in a clear, highly structured, and extensive report format, providing deep insights."
        )
        
        # 3. Parent initialization
        super().__init__(
            provider=provider,
            system_prompt=system_prompt,
            tools=tools,
            thread_id="deep_research_session",
            max_messages=max_messages,
            checkpointer=checkpointer
        )

        self._print_available_tools()

    @classmethod
    def from_env(cls) -> "ResearchAgent":
        source = os.getenv("AI_SOURCE", "ollama").lower()
        # For a researcher, a lower temperature is often preferred to keep facts straight.
        temperature = float(os.getenv("TEMPERATURE", "0.2")) 
        max_messages = int(os.getenv("MEMORY_MAX_MESSAGES", "50"))
        
        provider = AgentBase.build_provider(source, temperature)
        print(f"[ResearchAgent] Provider: {source.capitalize()} | temp: {temperature}")
        
        # In a real environment, you might want to fetch the checkpointer from context_provider
        # like in DefaultAgent, but keeping it simpler here if not strictly needed.
        # Let's cleanly inject it if available:
        try:
            from memory.context_provider import get_context_checkpointer
            checkpointer = get_context_checkpointer()
        except ImportError:
            checkpointer = None
            
        return cls(
            provider=provider,
            max_messages=max_messages,
            checkpointer=checkpointer
        )

    def as_tool(self) -> BaseTool:
        @tool("delegate_deep_research")
        def deep_research_tool(topic: str) -> str:
            """
            Delegate a deep research task to the Research Agent. Use this when a topic requires extensive investigation.
            
            Args:
                topic (str): The subject or topic to investigate deeply.
                
            Returns:
                str: A comprehensive, multi-faceted research report.
                
            Failure modes:
                - If the underlying agent fails, it throws or returns an error message as a string.
            """
            return self.run(topic)
        return deep_research_tool

            
        
    
