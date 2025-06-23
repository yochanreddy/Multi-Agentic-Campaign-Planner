from typing import Dict, Any
import yaml
from langchain.prompts import PromptTemplate
from langchain_community.chat_models import ChatOpenAI
from creative_planner.utils import get_required_env_var
from creative_planner.agents.base.process import BaseProcessNode
import logging

logger = logging.getLogger("creative_planner.agents.prompt_generator")

class PromptGenerator(BaseProcessNode):
    """Class for generating creative prompts."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the prompt generator.

        Args:
            config (Dict[str, Any]): Configuration dictionary
        """
        super().__init__(config)
        self.model_name = get_required_env_var("PROMPT_MODEL_NAME", "gpt-4")
        self.temperature = float(get_required_env_var("PROMPT_TEMPERATURE", "0.5"))

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the current state to generate creative prompts.

        Args:
            state (Dict[str, Any]): Current state as a dictionary

        Returns:
            Dict[str, Any]: Updated state with generated prompts
        """
        logger.info("\n" + "="*80)
        logger.info("🚀 STARTING PROMPT GENERATOR AGENT")
        logger.info("="*80)
        logger.info("📊 Initial State:")
        for key, value in state.items():
            logger.info(f"  - {key}: {value}")
        logger.info("="*80 + "\n")

        try:
            # Load the prompt template from YAML
            with open("creative_planner/agents/prompt_generator/prompt.yaml", "r") as f:
                prompt_config = yaml.safe_load(f)
            
            # Create a PromptTemplate from the YAML config
            prompt_template = PromptTemplate(
                template=prompt_config["template"],
                input_variables=prompt_config["input_variables"]
            )
            
            # Get the input variables from state
            input_vars = {
                var: state.get(var)
                for var in prompt_config["input_variables"]
            }
            
            # Format the prompt with the input variables
            formatted_prompt = prompt_template.format(**input_vars)
            
            # Initialize the LLM
            llm = ChatOpenAI(
                model_name=self.model_name,
                temperature=self.temperature
            )
            
            # Generate the system prompt using the LLM
            response = llm.invoke(formatted_prompt)
            system_prompt = response.content
            logger.info(f"System Prompt: {system_prompt}")
            
            # Update the state with the generated system prompt
            state["system_prompt"] = system_prompt
            
            logger.info("\n" + "="*80)
            logger.info("✅ COMPLETED PROMPT GENERATOR AGENT")
            logger.info("="*80)
            logger.info("📊 Final State:")
            for key, value in state.items():
                logger.info(f"  - {key}: {value}")
            logger.info("="*80 + "\n")
            
            return state
            
        except Exception as e:
            logger.error("\n" + "="*80)
            logger.error("❌ ERROR IN PROMPT GENERATOR AGENT")
            logger.error("="*80)
            logger.error("📊 Error State:")
            for key, value in state.items():
                logger.error(f"  - {key}: {value}")
            logger.error("="*80 + "\n")
            raise e 