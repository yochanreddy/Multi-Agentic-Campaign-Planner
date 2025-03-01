import os
import yaml

from utils import get_module_logger
from graph import CampaignPlanner
from langgraph.checkpoint.memory import MemorySaver
import uuid

# Load environment variables from .env file


logger = get_module_logger()


def load_config(file_name: str = "config.yaml") -> dict:
    with open(file_name, "r") as file:
        data = yaml.safe_load(file)
    return data


def main():
    config = load_config()
    config["LOG_LEVEL"] = os.getenv("LOG_LEVEL", "INFO")
    config["checkpointer"] = MemorySaver()
    graph = CampaignPlanner(config).get_compiled_graph()

    thread_config = {
        "configurable": {
            "thread_id": str(uuid.uuid4()),
            "global_parameters": {},
        }
    }

    for update in graph.invoke(
        {
            "brand_name": "Zepto",
            "website": "www.zeptonow.com",
            "brand_description": "Top 3 quick delivery service startup",
            "product_name": "Zepto Cafe",
            "product_description": "Zepto Cafe is a 10-minute food delivery service offering a diverse menu of freshly prepared snacks, beverages, and meals, combining speed and quality to cater to fast-paced urban lifestyles.",
        },
        config=thread_config,
        stream_mode="updates",
    ):
        for node_id, value in update.items():
            if "industry" in value:
                print(f"AI: {value['industry']}")


if __name__ == "__main__":
    main()
