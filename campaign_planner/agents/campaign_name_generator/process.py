from campaign_planner.agents.base import BaseProcessNode
from langchain_core.runnables.config import RunnableConfig
from .output import OutputNode
from campaign_planner.state import State
from campaign_planner.utils import get_module_logger

logger = get_module_logger()


class ProcessNode(BaseProcessNode):
    def __init__(
        self,
        config: dict,
        tools: list,
        model_name="OPENAI-GPT-4O",
        prompt_file_name="prompt.yaml",
    ):
        super().__init__(config, model_name, prompt_file_name)

        self.prompt.partial_variables["format_instructions"] = (
            OutputNode.output_parser.get_format_instructions()
        )
        self.agent = self.prompt | self.llm  # .bind_tools(tools=tools)

    async def process(self, state: State, config: RunnableConfig):
        logger.debug(f"{config['configurable']['thread_id']} start")
        response = await self.agent.ainvoke(state)
        logger.debug(f"{config['configurable']['thread_id']} finish")
        return {"messages": [response]}
