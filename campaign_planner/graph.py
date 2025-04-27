from langgraph.graph import StateGraph
from campaign_planner.agents.base import BaseGraph
from campaign_planner.agents.brand_industry_classifier import BrandIndustryClassifier
from campaign_planner.agents.audience_segment_analyzer import AudienceSegmentAnalyzer
from campaign_planner.agents.ad_channel_recommender import AdChannelRecommender
from campaign_planner.agents.campaign_schedule_recommender import (
    CampaignScheduleRecommender,
)
from campaign_planner.agents.marketing_budget_allocator import MarketingBudgetAllocator
from campaign_planner.agents.campaign_name_generator import CampaignNameGenerator
from campaign_planner.state import State


class CampaignPlanner(BaseGraph):
    def _build_graph(self):
        # Create nodes
        brand_industry_classifier = BrandIndustryClassifier(self.config)
        audience_segment_analyzer = AudienceSegmentAnalyzer(self.config)
        ad_channel_recommender = AdChannelRecommender(self.config)
        campaign_schedule_recommender = CampaignScheduleRecommender(self.config)
        marketing_budget_allocator = MarketingBudgetAllocator(self.config)
        campaign_name_generator = CampaignNameGenerator(self.config)

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
        graph.add_node(
            "marketing_budget_allocator",
            marketing_budget_allocator.get_compiled_graph(),
        )
        graph.add_node(
            "campaign_name_generator",
            campaign_name_generator.get_compiled_graph(),
        )

        # Add edges
        graph.add_edge("brand_industry_classifier", "audience_segment_analyzer")
        graph.add_edge("audience_segment_analyzer", "ad_channel_recommender")
        graph.add_edge("ad_channel_recommender", "campaign_schedule_recommender")
        graph.add_edge("campaign_schedule_recommender", "marketing_budget_allocator")
        graph.add_edge("marketing_budget_allocator", "campaign_name_generator")

        # Add start and end points
        graph.set_entry_point("brand_industry_classifier")
        graph.set_finish_point("campaign_name_generator")

        return graph

    def get_input_schema(self) -> type:
        return None

    def get_output_schema(self) -> type:
        return None
