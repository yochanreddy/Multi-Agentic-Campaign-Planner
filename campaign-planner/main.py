import os
from pathlib import Path
import yaml
from utils import setup_logger

os.environ["PROJECT_NAME"] = Path(__file__).parent.name

logger = setup_logger(f"{os.getenv('PROJECT_NAME', 'root')}")


def load_config(file_name: str = "config.yaml") -> dict:
    with open(file_name, "r") as file:
        data = yaml.safe_load(file)
    return data


def main():
    config = load_config()
    print("Hello from campaign-planner!")


if __name__ == "__main__":
    main()
