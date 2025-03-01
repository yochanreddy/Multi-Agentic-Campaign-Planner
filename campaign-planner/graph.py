from langgraph.graph import StateGraph
from agents.base import Graph
from agents.brand_mapping import BrandMappingGraph
from state import State


class CampaignPlanner(Graph):
    def _build_graph(self):
        # Create nodes
        brand_mapper = BrandMappingGraph(self.config)

        # Create graph
        graph = StateGraph(State)

        # Add nodes
        graph.add_node("brand_mapping", brand_mapper.get_compiled_graph())

        # Add edges
        # pass

        # Add start and end points
        graph.set_entry_point("brand_mapping")
        graph.set_finish_point("brand_mapping")

        return graph

    def get_input_schema(self) -> type:
        return None

    def get_output_schema(self) -> type:
        return None
