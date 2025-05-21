from typing import Annotated, Dict, TypedDict, Optional, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from .state import State
from .agents.objective_planner import ObjectivePlannerAgent
import logging

logger = logging.getLogger(__name__)

class GraphInput(TypedDict, total=False):
    brand_name: str
    brand_description: str
    website_url: str
    user_prompt: Optional[str]

class CampaignObjectiveGraph:
    """Main graph implementation for campaign objective planner workflow"""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the graph with configuration"""
        self.config = config
        self.graph = None
        self.logger = logging.getLogger(__name__)
        self.objective_planner = ObjectivePlannerAgent()

    def _build_graph(self) -> StateGraph:
        """Build the graph structure for campaign objective planning."""
        # Create the graph
        graph = StateGraph(State)

        # Add the objective planner node
        def objective_planner(state: Dict) -> Dict:
            try:
                logger.info("Starting objective planner node")
                logger.info(f"Input state: {state}")
                result = self.objective_planner.process(state)
                logger.info(f"Objective planner result: {result}")
                return result
            except Exception as e:
                logger.error(f"Error in objective planner node: {str(e)}")
                logger.error(f"Error type: {type(e)}")
                logger.error(f"Error details: {e.__dict__ if hasattr(e, '__dict__') else 'No details available'}")
                raise

        graph.add_node("objective_planner", objective_planner)

        # Set the entry point
        graph.set_entry_point("objective_planner")

        # Add edges
        graph.add_edge("objective_planner", END)

        # Configure state passing
        graph.config = {
            "recursion_limit": 1,
            "state_updates": {
                "objective_planner": {
                    "next": None,
                    "state": lambda x: x
                }
            }
        }

        return graph

    def get_compiled_graph(self) -> StateGraph:
        """Return the compiled graph"""
        graph = self._build_graph()
        return graph.compile(
            checkpointer=self.config.get("checkpointer", MemorySaver()),
            debug=(self.config.get("LOG_LEVEL", "INFO") == "DEBUG")
        )
