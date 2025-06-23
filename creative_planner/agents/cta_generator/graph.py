from typing import Any, Dict
from langgraph.graph import StateGraph
from creative_planner.agents.base.graph import BaseGraph
from creative_planner.agents.cta_generator.process import CTAGenerator
from creative_planner.state import State


class CTAGeneratorGraph(BaseGraph):
    """Graph implementation for CTA generator agent"""

    def _build_graph(self) -> StateGraph:
        """
        Build the graph structure for CTA generation.

        Returns:
            StateGraph: Configured graph for CTA generation
        """
        # Create the graph
        graph = StateGraph(state_schema=State)

        # Create the node
        cta_generator = CTAGenerator(self.config)

        # Add the node to the graph
        graph.add_node("cta_generator", cta_generator.process)

        # Set both entry and finish points to the CTA generator node
        graph.set_entry_point("cta_generator")
        graph.set_finish_point("cta_generator")

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