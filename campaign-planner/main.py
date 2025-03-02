import os
from langgraph.types import Command
from utils import load_config, get_module_logger, draw_mermaid_graph
from graph import CampaignPlanner
from langgraph.checkpoint.memory import MemorySaver
import uuid
import time

logger = get_module_logger()


def initialize_graph():
    graph = CampaignPlanner(config).get_compiled_graph()
    if os.getenv("LOG_LEVEL").lower() == "debug":
        draw_mermaid_graph(graph)
    return graph


def run_graph(thread_config, data, first_run=False):
    if first_run:
        for event in graph.stream(data, config=thread_config):
            if "__interrupt__" in event:
                current_state = graph.get_state(thread_config)
                current_node = current_state.next[0]
                return current_node, event["__interrupt__"][0].value.model_dump()
    else:
        for event in graph.stream(Command(resume=data), config=thread_config):
            if "__interrupt__" in event:
                current_state = graph.get_state(thread_config)
                current_node = current_state.next[0]
                return current_node, event["__interrupt__"][0].value.model_dump()

    return None, None


def main():
    thread_config = {
        "configurable": {
            "thread_id": str(uuid.uuid4()),
            "global_parameters": {},
        }
    }
    input_data = {
        "brand_name": "Zepto",
        "website": "www.zeptonow.com",
        "brand_description": "Top 3 quick delivery service startup",
        "product_name": "Zepto Cafe",
        "product_description": "Zepto Cafe is a 10-minute food delivery service offering a diverse menu of freshly prepared snacks, beverages, and meals, combining speed and quality to cater to fast-paced urban lifestyles.",
        "campaign_objective": "Increase Brand Awareness",
        "integrated_ad_platforms": ["Meta", "Google"],
    }
    start_time = time.time()

    current_node, validation_data = run_graph(thread_config, input_data, first_run=True)
    pass

    while current_node:
        current_node, validation_data = run_graph(thread_config, validation_data)
        pass

    # for update in graph.invoke(
    # input_data,
    #     config=thread_config,
    #     stream_mode="updates",
    # ):
    #     for node_id, value in update.items():
    #         print("*" * 10)
    #         print(f"AI: {value['messages'][-1].content}")
    #         print("#" * 10)
    logger.info("total runtime %f", time.time() - start_time)


if __name__ == "__main__":
    config = load_config()
    config["LOG_LEVEL"] = os.getenv("LOG_LEVEL", "INFO")
    config["checkpointer"] = MemorySaver()
    graph = initialize_graph()
    main()
