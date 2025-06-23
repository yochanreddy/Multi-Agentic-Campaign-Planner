from typing import Annotated, Any, Dict
from campaign_planner.utils import get_module_logger
from langchain_openai import ChatOpenAI

logger = get_module_logger()


class Generator:
    """Handles model initialization and retrieval for language models."""

    DEFAULT_MODEL = "OPENAI-GPT-4O"

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize Generator with configuration.

        Args:
            config: Configuration dictionary containing model settings
        """
        try:
            openai_config = config["OPENAI"]["COMPLETION"]
            openai_model = ChatOpenAI(
                model=openai_config["MODEL_NAME"],
                temperature=openai_config["TEMPERATURE"],
                max_completion_tokens=openai_config["MAX_TOKENS"],
                streaming=openai_config["STREAMING"],
            )

            self.models = {
                f"OPENAI-{openai_config['MODEL_NAME'].upper()}": openai_model
            }

        except KeyError as e:
            logger.error(f"Missing configuration key: {e}")
            raise ValueError(f"Invalid configuration: missing {e}")

    def get_model(
        self,
        name: Annotated[str, "format: provider-model_name"] = DEFAULT_MODEL,
    ) -> ChatOpenAI:
        """
        Retrieve a model by name.

        Args:
            name: Model identifier in format 'provider-model_name'

        Returns:
            ChatOpenAI: The requested model instance

        Raises:
            KeyError: If model name is not found
        """
        try:
            return self.models[name]
        except KeyError:
            logger.warning(
                f"Model {name} not found, using default: {self.DEFAULT_MODEL}"
            )
            return self.models[self.DEFAULT_MODEL]
