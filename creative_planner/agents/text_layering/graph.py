from langgraph.graph import StateGraph
from creative_planner.agents.base.graph import BaseGraph
from creative_planner.agents.text_layering.process import TextLayeringProcess
from creative_planner.state import State


class TextLayeringGraph(BaseGraph):
    """Graph implementation for text layering workflow"""

    def _build_graph(self) -> StateGraph:
        """
        Build the graph structure for text layering.

        Returns:
            StateGraph: Configured graph for text layering
        """
        # Create the graph
        graph = StateGraph(State)

        # Create the process
        text_layering = TextLayeringProcess(self.config)

        # Add the node to the graph
        graph.add_node(
            "text_layering",
            text_layering.process
        )

        # Set the entry point
        graph.set_entry_point("text_layering")

        # Set the finish point
        graph.set_finish_point("text_layering")

        # Configure state passing using the correct method
        graph.config = {
            "recursion_limit": 1,
            "state_updates": {
                "text_layering": {
                    "next": None,
                    "state": lambda x: x
                }
            }
        }

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