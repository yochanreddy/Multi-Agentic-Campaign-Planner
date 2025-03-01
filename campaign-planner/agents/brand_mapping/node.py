import os
from pathlib import Path
from typing import Any, Dict
from agents.base import InputNode, ProcessNode, OutputNode
from langchain_core.runnables.config import RunnableConfig
from .schema import InputSchema, OutputSchema
from .state import State
from langchain_core.messages import AIMessage
from utils import setup_logger

logger = setup_logger(
    f"{os.getenv('PROJECT_NAME', 'root')}.{Path(__file__).parent.name}"
)


class Input(InputNode):
    def validate_and_parse(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and parse input state"""
        input_data = InputSchema(state)
        logger.debug("Received: ", input_data)
        return {"input": input_data}


class Process(ProcessNode):
    def __init__(self, config, prompt_file_name="prompt.yaml"):
        super().__init__(config, prompt_file_name)

    def __call__(self, state: State, config: RunnableConfig):
        logger.debug("processing...")
        return {"messages": [AIMessage("hello.")]}


class Output(OutputNode):
    def format_output(self, state: Dict[str, Any]) -> OutputSchema:
        """Format the output state"""
        logger.debug("Sending: ", {state["output"]})
        return state["output"]
