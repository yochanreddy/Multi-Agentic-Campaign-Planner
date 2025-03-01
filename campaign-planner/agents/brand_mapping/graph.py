from langgraph.graph import StateGraph
from agents.base import Graph
from .node import Input, Output, Process
from .schema import InputSchema, OutputSchema


class BrandMappingGraph(Graph):
    def _build_graph(self) -> StateGraph:
        # Create nodes
        input_node = Input()
        process_node = Process()
        output_node = Output()

        # Create graph
        graph = StateGraph()

        # Add nodes
        graph.add_node("input", input_node.validate_and_parse)
        graph.add_node("process", process_node.process)
        graph.add_node("output", output_node.format_output)

        # Add edges
        graph.add_edge("input", "process")
        graph.add_edge("process", "output")

        # Add start and end points
        graph.set_entry_point("input")
        graph.set_finish_point("output")

        return graph

    def get_input_schema(self) -> type:
        return InputSchema

    def get_output_schema(self) -> type:
        return OutputSchema
