from abc import ABC, abstractmethod
from typing import Dict, Any
from langgraph.graph import StateGraph


class Graph(ABC):
    """Base class for agent sub-graphs"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    def _build_graph(
        self,
    ) -> StateGraph:
        """Build the internal IPO graph structure"""
        pass

    @abstractmethod
    def get_input_schema(self) -> Any:
        """Define input schema for the agent"""
        pass

    @abstractmethod
    def get_output_schema(self) -> Any:
        """Define output schema for the agent"""
        pass

    def get_compiled_graph(self) -> StateGraph:
        """Return the compiled graph"""
        graph = self._build_graph()
        return graph.compile(
            checkpointer=self.config["checkpointer"],
            debug=(self.config["LOG_LEVEL"] == "DEBUG"),
        )
