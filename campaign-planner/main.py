import yaml
from utils import setup_logger

logger = setup_logger("campaign_planner")


def load_config(file_name: str = "config.yaml") -> dict:
    with open(file_name, "r") as file:
        data = yaml.safe_load(file)
    return data


def main():
    config = load_config()
    print("Hello from campaign-planner!")


if __name__ == "__main__":
    main()
