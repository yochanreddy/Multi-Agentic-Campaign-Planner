from nodes.base_node import BaseNode
from langchain_core.runnables.config import RunnableConfig


class BrandMapper(BaseNode):
    def __init__(self, config, prompt_file_name="prompt.yaml"):
        super().__init__(config, prompt_file_name)

    def __call__(self, state: State, config: RunnableConfig):
        return super().__call__(state)
