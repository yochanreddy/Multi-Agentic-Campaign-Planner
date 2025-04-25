from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from creative_planner.utils import get_module_logger

logger = get_module_logger()

class BaseGraph(ABC):
    """Base class for all workflow graphs"""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the graph with configuration"""
        self.config = config
        self.graph = None
        self.logger = get_module_logger()

    @abstractmethod
    def _build_graph(self) -> Dict[str, Any]:
        """Build the graph structure"""
        pass

    @abstractmethod
    def get_input_schema(self) -> Optional[Dict[str, Any]]:
        """Get the input schema for the graph"""
        pass

    @abstractmethod
    def get_output_schema(self) -> Optional[Dict[str, Any]]:
        """Get the output schema for the graph"""
        pass

    def get_compiled_graph(self) -> CompiledStateGraph:
        """Return the compiled graph"""
        graph = self._build_graph()
        return graph.compile(
            checkpointer=self.config["checkpointer"],
            debug=(self.config["LOG_LEVEL"] == "DEBUG"),
        ) 