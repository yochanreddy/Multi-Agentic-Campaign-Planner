from typing import Dict, Any
import yaml
from langchain.prompts import PromptTemplate
from langchain_community.chat_models import ChatOpenAI
from creative_planner.state import State

class PromptGenerator:
    """Class for generating creative prompts."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the prompt generator.

        Args:
            config (Dict[str, Any]): Configuration dictionary
        """
        self.config = config

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the current state to generate creative prompts.

        Args:
            state (Dict[str, Any]): Current state as a dictionary

        Returns:
            Dict[str, Any]: Updated state with generated prompts
        """
        print("\n" + "="*80)
        print("🚀 STARTING PROMPT GENERATOR AGENT")
        print("="*80)
        print("📊 Initial State:")
        for key, value in state.items():
            print(f"  - {key}: {value}")
        print("="*80 + "\n")

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
                model_name="gpt-4-turbo-preview",
                temperature=0.7
            )
            
            # Generate the system prompt using the LLM
            response = llm.invoke(formatted_prompt)
            system_prompt = response.content
            
            # Update the state with the generated system prompt
            state["system_prompt"] = system_prompt
            
            print("\n" + "="*80)
            print("✅ COMPLETED PROMPT GENERATOR AGENT")
            print("="*80)
            print("📊 Final State:")
            for key, value in state.items():
                print(f"  - {key}: {value}")
            print("="*80 + "\n")
            
            return state
            
        except Exception as e:
            print("\n" + "="*80)
            print("❌ ERROR IN PROMPT GENERATOR AGENT")
            print("="*80)
            print("📊 Error State:")
            for key, value in state.items():
                print(f"  - {key}: {value}")
            print("="*80 + "\n")
            raise e 