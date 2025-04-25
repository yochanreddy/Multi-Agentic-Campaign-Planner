from typing import Any, Dict
from langgraph.graph import StateGraph
from creative_planner.agents.base.graph import BaseGraph
from creative_planner.agents.prompt_generator.process import PromptGenerator
from creative_planner.state import State


class PromptGeneratorGraph(BaseGraph):
    """Graph implementation for the prompt generator agent"""

    def _build_graph(self) -> StateGraph:
        """
        Build the graph structure for prompt generation.

        Returns:
            StateGraph: Configured graph for prompt generation
        """
        # Create the graph
        graph = StateGraph(State)

        # Create the prompt generator node
        prompt_generator = PromptGenerator(self.config)

        # Add the node to the graph
        graph.add_node("prompt_generator", prompt_generator.process)

        # Set the entry and finish points
        graph.set_entry_point("prompt_generator")
        graph.set_finish_point("prompt_generator")

        return graph

    def get_input_schema(self) -> type:
        """
        Get the input schema for the graph.

        Returns:
            type: The State class
        """
        return State

    def get_output_schema(self) -> type:
        """
        Get the output schema for the graph.

        Returns:
            type: The State class
        """
        return State 