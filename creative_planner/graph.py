from langgraph.graph import StateGraph
from creative_planner.agents.base.graph import BaseGraph
from creative_planner.agents.prompt_generator.graph import PromptGeneratorGraph
from creative_planner.agents.image_generator.graph import ImageGeneratorGraph
from creative_planner.agents.image_analyzer.graph import ImageAnalyzerGraph
from creative_planner.agents.mask_generator.graph import MaskGeneratorGraph
from creative_planner.agents.cta_generator.graph import CTAGeneratorGraph
from creative_planner.agents.text_layering.graph import TextLayeringGraph
from creative_planner.state import State


class CreativePlanner(BaseGraph):
    """Main graph implementation for creative planner workflow"""

    def _build_graph(self) -> StateGraph:
        """
        Build the graph structure for creative planning.

        Returns:
            StateGraph: Configured graph for creative planning
        """
        # Create the graph
        graph = StateGraph(State)

        # Create the nodes
        prompt_generator = PromptGeneratorGraph(self.config)
        image_generator = ImageGeneratorGraph(self.config)
        image_analyzer = ImageAnalyzerGraph(self.config)
        mask_generator = MaskGeneratorGraph(self.config)
        cta_generator = CTAGeneratorGraph(self.config)
        text_layering = TextLayeringGraph(self.config)

        # Add the nodes to the graph
        graph.add_node(
            "prompt_generator",
            prompt_generator.get_compiled_graph()
        )
        graph.add_node(
            "image_generator",
            image_generator.get_compiled_graph()
        )
        graph.add_node(
            "image_analyzer",
            image_analyzer.get_compiled_graph()
        )
        graph.add_node(
            "mask_generator",
            mask_generator.get_compiled_graph()
        )
        graph.add_node(
            "cta_generator",
            cta_generator.get_compiled_graph()
        )
        graph.add_node(
            "text_layering",
            text_layering.get_compiled_graph()
        )

        # Set the entry point
        graph.set_entry_point("prompt_generator")

        # Add edges
        graph.add_edge("prompt_generator", "image_generator")
        graph.add_edge("image_generator", "image_analyzer")
        graph.add_edge("image_analyzer", "mask_generator")
        graph.add_edge("mask_generator", "cta_generator")
        graph.add_edge("cta_generator", "text_layering")

        # Set the finish point
        graph.set_finish_point("text_layering")

        # Configure state passing using the correct method
        graph.config = {
            "recursion_limit": 1,
            "state_updates": {
                "prompt_generator": {
                    "next": "image_generator",
                    "state": lambda x: x
                },
                "image_generator": {
                    "next": "image_analyzer",
                    "state": lambda x: x
                },
                "image_analyzer": {
                    "next": "mask_generator",
                    "state": lambda x: x
                },
                "mask_generator": {
                    "next": "cta_generator",
                    "state": lambda x: x
                },
                "cta_generator": {
                    "next": "text_layering",
                    "state": lambda x: x
                },
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