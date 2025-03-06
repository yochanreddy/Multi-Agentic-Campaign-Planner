from langgraph.graph import StateGraph
from campaign_planner.agents.base import BaseGraph
from .input import InputSchema, InputNode
from .output import OutputSchema, OutputNode
from .process import ProcessNode
from .router import RouterNode
from .human import HumanNode
from campaign_planner.state import State
from langchain_core.tools.retriever import create_retriever_tool
from campaign_planner.utils import Retriever, get_module_logger
from langgraph.prebuilt import ToolNode
from langchain_core.prompts import PromptTemplate

logger = get_module_logger()


class BrandIndustryClassifier(BaseGraph):
    def __init__(self, config):
        super().__init__(config)
        # Initialize the retriever
        retriever = Retriever(config)

        # Initialize the database (this will generate descriptions and store embeddings if they don't exist)
        retriever.initialize_database()

        self.tools = [
            create_retriever_tool(
                retriever.get_retriever(),
                name="get_industry_types",
                description="Suggests 5 type of industry based on the brand description by performing a Maximum Marginal Relevance Search on the vectorstore",
                document_prompt=PromptTemplate.from_template("Industry 1: {category}"),
            )
        ]

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
