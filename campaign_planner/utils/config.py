import yaml


def load_config(file_name: str = "config.yaml") -> dict:
    with open(file_name, "r") as file:
        data = yaml.safe_load(file)
    return data
