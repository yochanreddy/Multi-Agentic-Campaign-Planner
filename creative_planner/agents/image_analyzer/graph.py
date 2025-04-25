from typing import Any, Dict
from langgraph.graph import StateGraph
from creative_planner.agents.base.graph import BaseGraph
from creative_planner.agents.image_analyzer.process import ImageAnalyzer
from creative_planner.state import State


class ImageAnalyzerGraph(BaseGraph):
    """Graph implementation for the image analyzer agent"""

    def _build_graph(self) -> StateGraph:
        """
        Build the graph structure for image analysis.

        Returns:
            StateGraph: Configured graph for image analysis
        """
        # Create the graph
        graph = StateGraph(State)

        # Create the image analyzer node
        image_analyzer = ImageAnalyzer(self.config)

        # Add the node to the graph
        graph.add_node("image_analyzer", image_analyzer.process)

        # Set the entry and finish points
        graph.set_entry_point("image_analyzer")
        graph.set_finish_point("image_analyzer")

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