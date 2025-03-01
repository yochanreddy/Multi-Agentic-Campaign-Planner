from langgraph.graph import StateGraph
from agents.base import Graph
from agents.brand_industry_classifier import BrandIndustryClassifier
from state import State


class CampaignPlanner(Graph):
    def _build_graph(self):
        # Create nodes
        brand_industry_classifier = BrandIndustryClassifier(self.config)

        # Create graph
        graph = StateGraph(State)

        # Add nodes
        graph.add_node(
            "brand_industry_classifier", brand_industry_classifier.get_compiled_graph()
        )

        # Add edges
        # pass

        # Add start and end points
        graph.set_entry_point("brand_industry_classifier")
        graph.set_finish_point("brand_industry_classifier")

        return graph

    def get_input_schema(self) -> type:
        return None

    def get_output_schema(self) -> type:
        return None
