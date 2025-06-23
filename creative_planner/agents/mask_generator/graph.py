from typing import Dict, Any
from creative_planner.agents.base.graph import BaseGraph
from creative_planner.agents.base.graph import StateGraph
from creative_planner.agents.mask_generator.process import MaskGenerator
from creative_planner.state import State


class MaskGeneratorGraph(BaseGraph):
    """Graph implementation for mask generator agent"""

    def _build_graph(self) -> StateGraph:
        """
        Build the graph structure for mask generation.

        Returns:
            StateGraph: Configured graph for mask generation
        """
        # Create the graph
        graph = StateGraph(state_schema=State)

        # Create the node
        mask_generator = MaskGenerator(self.config)

        # Add the node to the graph with the process method
        graph.add_node("mask_generator", mask_generator.process)

        # Set both entry and finish points to the mask generator node
        graph.set_entry_point("mask_generator")
        graph.set_finish_point("mask_generator")

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