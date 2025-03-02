from langgraph.graph import StateGraph
from agents.base import BaseGraph
from .input import InputSchema, InputNode
from .output import OutputSchema, OutputNode
from .process import ProcessNode
from .router import RouterNode
from .human import HumanNode
from state import State
from utils import get_module_logger
from langgraph.prebuilt import ToolNode

logger = get_module_logger()


class AudienceSegmentAnalyzer(BaseGraph):
    def __init__(self, config):
        super().__init__(config)
        self.tools = []

    def _build_graph(self) -> StateGraph:
        # Create nodes
        input_node = InputNode()
        process_node = ProcessNode(self.config, self.tools)
        output_node = OutputNode()
        human_node = HumanNode()
        router_node = RouterNode()
        tool_node = ToolNode(self.tools)

        # Create graph
        graph = StateGraph(State)

        # Add nodes
        graph.add_node("input_node", input_node.validate_and_parse)
        graph.add_node("process_node", process_node.process)
        graph.add_node("output_node", output_node.format_output)
        graph.add_node("human_node", human_node.get_human_validation)
        graph.add_node("tool_node", tool_node)

        # Add edges
        graph.add_edge("input_node", "process_node")
        graph.add_conditional_edges(
            "process_node",
            router_node.determine_next_step,
            {"tool": "tool_node", "finish": "output_node"},
        )
        graph.add_edge("tool_node", "process_node")
        graph.add_edge("output_node", "human_node")

        # Add start and end points
        graph.set_entry_point("input_node")
        graph.set_finish_point("human_node")

        return graph

    def get_input_schema(self) -> type:
        return InputSchema

    def get_output_schema(self) -> type:
        return OutputSchema
