from typing import Any, Dict
from langgraph.graph import StateGraph
from creative_planner.agents.base.graph import BaseGraph
from creative_planner.agents.image_generator.process import ImageGenerator
from creative_planner.state import State


class ImageGeneratorGraph(BaseGraph):
    """Graph implementation for the image generator agent"""

    def _build_graph(self) -> StateGraph:
        """
        Build the graph structure for image generation.

        Returns:
            StateGraph: Configured graph for image generation
        """
        # Create the graph
        graph = StateGraph(State)

        # Create the image generator node
        image_generator = ImageGenerator(self.config)

        # Add the node to the graph
        graph.add_node("image_generator", image_generator.process)

        # Set the entry and finish points
        graph.set_entry_point("image_generator")
        graph.set_finish_point("image_generator")

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