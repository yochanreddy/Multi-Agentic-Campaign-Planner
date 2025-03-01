import os

from utils import load_config, get_module_logger, draw_mermaid_graph
from graph import CampaignPlanner
from langgraph.checkpoint.memory import MemorySaver
import uuid
import time

logger = get_module_logger()


def main():
    config = load_config()
    config["LOG_LEVEL"] = os.getenv("LOG_LEVEL", "INFO")
    config["checkpointer"] = MemorySaver()
    graph = CampaignPlanner(config).get_compiled_graph()
    if os.getenv("LOG_LEVEL").lower() == "debug":
        draw_mermaid_graph(graph)

    thread_config = {
        "configurable": {
            "thread_id": str(uuid.uuid4()),
            "global_parameters": {},
        }
    }
    start_time = time.time()
    for update in graph.invoke(
        {
            "brand_name": "Zepto",
            "website": "www.zeptonow.com",
            "brand_description": "Top 3 quick delivery service startup",
            "product_name": "Zepto Cafe",
            "product_description": "Zepto Cafe is a 10-minute food delivery service offering a diverse menu of freshly prepared snacks, beverages, and meals, combining speed and quality to cater to fast-paced urban lifestyles.",
            "campaign_objective": "Increase Brand Awareness",
            "integrated_ad_platforms": ["Meta", "Google"],
        },
        config=thread_config,
        stream_mode="updates",
    ):
        for node_id, value in update.items():
            print("*" * 10)
            print(f"AI: {value['messages'][-1].content}")
            print("#" * 10)
    logger.info("total runtime %f", time.time() - start_time)


if __name__ == "__main__":
    main()
