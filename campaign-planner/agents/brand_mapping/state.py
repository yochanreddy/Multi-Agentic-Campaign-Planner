from langgraph.graph import MessagesState
from .schema import InputSchema, OutputSchema


class State(MessagesState):
    input: InputSchema
    output: OutputSchema
