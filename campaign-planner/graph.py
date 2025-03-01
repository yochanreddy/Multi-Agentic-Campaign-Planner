from langgraph.graph import StateGraph
from agents.base import Graph
from agents.brand_industry_classifier import BrandIndustryClassifier
from agents.audience_segment_analyzer import AudienceSegmentAnalyzer
from agents.ad_channel_recommender import AdChannelRecommender
from agents.campaign_schedule_recommender import CampaignScheduleRecommender
from state import State


class CampaignPlanner(Graph):
    def _build_graph(self):
        # Create nodes
        brand_industry_classifier = BrandIndustryClassifier(self.config)
        audience_segment_analyzer = AudienceSegmentAnalyzer(self.config)
        ad_channel_recommender = AdChannelRecommender(self.config)
        campaign_schedule_recommender = CampaignScheduleRecommender(self.config)

        # Create graph
        graph = StateGraph(State)

        # Add nodes
        graph.add_node(
            "brand_industry_classifier", brand_industry_classifier.get_compiled_graph()
        )
        graph.add_node(
            "audience_segment_analyzer", audience_segment_analyzer.get_compiled_graph()
        )
        graph.add_node(
            "ad_channel_recommender", ad_channel_recommender.get_compiled_graph()
        )
        graph.add_node(
            "campaign_schedule_recommender",
            campaign_schedule_recommender.get_compiled_graph(),
        )

        # Add edges
        graph.add_edge("brand_industry_classifier", "audience_segment_analyzer")
        graph.add_edge("audience_segment_analyzer", "ad_channel_recommender")
        graph.add_edge("ad_channel_recommender", "campaign_schedule_recommender")

        # Add start and end points
        graph.set_entry_point("brand_industry_classifier")
        graph.set_finish_point("campaign_schedule_recommender")

        return graph

    def get_input_schema(self) -> type:
        return None

    def get_output_schema(self) -> type:
        return None
