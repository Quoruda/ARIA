from typing import TypedDict, List
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END

from brain.agent_base import AgentBase

class PlanExecuteState(TypedDict):
    """The graph state schema for Plan-and-Execute."""
    initial_goal: str
    plan: List[str]
    action_history: List[str]
    final_response: str

class PlanExecuteBase(AgentBase):
    """
    Abstract base class for agents requiring planning
    and executing multi-step tasks.
    """

    def _build_agent(self):
        """Builds the Plan-and-Execute state graph. Identical for ALL children."""
        builder = StateGraph(PlanExecuteState)

        # 1. Add nodes
        builder.add_node("planner", self._planner_node)
        builder.add_node("worker", self._worker_node)
        builder.add_node("replanner", self._replanner_node)

        # 2. Main wiring
        builder.add_edge(START, "planner")
        builder.add_edge("planner", "worker")
        builder.add_edge("worker", "replanner")

        # 3. Router (The loop condition)
        def route_replanner(state: PlanExecuteState):
            # If we have a final response, we are finished!
            if state.get("final_response"):
                return END
            # Otherwise, return to work on the next task
            return "worker"

        builder.add_conditional_edges("replanner", route_replanner)

        return builder.compile(checkpointer=self.checkpointer)

    # ==========================================
    # GRAPH NODES (Business logic)
    # ==========================================

    def _planner_node(self, state: PlanExecuteState):
        """Takes the goal and generates a strict list of tasks (JSON)."""
        # Define expected format to force the LLM
        class Plan(BaseModel):
            tasks: List[str] = Field(description="List of steps to follow.")

        llm = self.provider.get_model().with_structured_output(Plan)

        prompt = f"""You are an expert planner.
        Your goal: {state.get('initial_goal')}
        Break down this goal into a list of simple steps. You must only plan."""

        result = llm.invoke(prompt)
        return {"plan": result.tasks} # Initialize the plan

    def _worker_node(self, state: PlanExecuteState):
        """Takes the FIRST task of the plan and executes it with tools."""
        current_task = state["plan"][0]

        # Here, create a very ephemeral "mini-agent" just for this task
        # It has access to the tools of the child class (self.tools)
        llm_with_tools = self.provider.get_model().bind_tools(self.tools)

        prompt = f"""You are a worker.
        Global goal: {state.get('initial_goal')}
        What has already been done: {state.get('action_history', [])}
        
        Your immediate task: {current_task}
        Use your tools to accomplish it and provide the result."""

        # (In complete production code, we would use a ToolNode here to manage tools)
        response = llm_with_tools.invoke(prompt)

        # Add the result to the history
        return {"action_history": [f"Task '{current_task}' completed. Result: {response.content}"]}

    def _replanner_node(self, state: PlanExecuteState):
        """Checks if we are done, updates the plan, or drafts the final response."""
        # Remove the task we just completed
        new_plan = state["plan"][1:]

        # If there are no more tasks, it's time to review!
        if len(new_plan) == 0:
            llm = self.provider.get_model()
            final_prompt = f"""The goal was: {state.get('initial_goal')}.
            Here is everything that was found/done: {state.get('action_history')}
            Write a complete and structured final response for the user."""

            response = llm.invoke(final_prompt)
            return {"plan": [], "final_response": response.content}

        # Otherwise, simply return the updated plan (which will trigger the loop)
        return {"plan": new_plan}

    # ==========================================
    # OVERRIDE PUBLIC INTERFACE
    # ==========================================
    
    def get_response(self, user_input: str) -> str:
        """Invokes the agent and returns the final response as a string."""
        # We need to adapt the inputs to our PlanExecuteState
        inputs = {
            "initial_goal": user_input, 
            "plan": [], 
            "action_history": [], 
            "final_response": ""
        }
        response = self._agent.invoke(inputs, config=self._make_config())
        return response.get("final_response", "")

    def stream(self, user_input: str):
        """Yields response chunks from the agent (streaming)."""
        # The default implementation streams 'messages'. 
        return super().stream(user_input)
