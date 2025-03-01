from agents.base import ProcessNode
from langchain_core.runnables.config import RunnableConfig
from .output import Output
from .state import LocalState
from utils import get_module_logger

logger = get_module_logger()


class Process(ProcessNode):
    def __init__(
        self,
        config: dict,
        tools: list,
        model_name="OPENAI-GPT-4O",
        prompt_file_name="prompt.yaml",
    ):
        super().__init__(config, model_name, prompt_file_name)

        self.prompt.partial_variables["format_instructions"] = (
            Output.output_parser.get_format_instructions()
        )
        self.agent = self.prompt | self.llm.bind_tools(tools=tools)

    def process(self, state: LocalState, config: RunnableConfig):
        logger.debug(f"{self.__class__.__name__} start")
        response = self.agent.invoke(state)
        logger.debug(f"{self.__class__.__name__} finish")
        return {"messages": [response]}
