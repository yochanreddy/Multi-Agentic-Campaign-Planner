from typing import Dict, Any
from creative_planner.agents.base.process import BaseProcessNode
from creative_planner.state import State
from creative_planner.utils.error_handler import NyxAIException
from creative_planner.utils.logger import setup_logger
from creative_planner.utils.config import config
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field, validator
import logging
import re
import yaml
import os
from pathlib import Path

class CTAResponse(BaseModel):
    """Pydantic model for CTA response validation"""
    headline: str = Field(..., min_length=1, description="The main headline text")
    subheadline: str = Field(..., min_length=1, description="The subheadline text")
    cta: str = Field(..., min_length=1, description="The call-to-action text")

    @validator('headline', 'subheadline', 'cta')
    def clean_text(cls, v):
        """Clean text by removing quotes and extra whitespace"""
        return v.strip().strip('"')

class CTAGenerator(BaseProcessNode):
    """Process implementation for CTA generator agent"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, model_name="gpt-4")
        self.logger = setup_logger(__name__)
        self._load_prompt_template()
        
    def _load_prompt_template(self):
        """Load the prompt template from YAML file"""
        try:
            current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
            prompt_path = current_dir / "prompt.yaml"
            
            with open(prompt_path, 'r') as f:
                prompt_config = yaml.safe_load(f)
                
            self.prompt_template = PromptTemplate(
                template=prompt_config["template"],
                input_variables=prompt_config["input_variables"]
            )
            
        except Exception as e:
            self.logger.error(f"Error loading prompt template: {str(e)}")
            raise NyxAIException(
                internal_code=7108,
                message="Error loading prompt template",
                detail=f"7108: {str(e)}"
            )
            
    def _parse_response(self, response: str) -> Dict[str, str]:
        """Parse the response to extract headline, subheadline, and CTA using Pydantic"""
        try:
            # Log the raw response for debugging
            self.logger.debug(f"Raw response from LLM: {response}")
            
            # Clean up the response by removing any leading/trailing whitespace
            response = response.strip()
            
            # Initialize data dictionary
            data = {}
            
            # Define patterns for each field
            patterns = {
                'headline': [
                    r'(?i)headline\s*:\s*"([^"]*)"',
                    r'(?i)headline\s*:\s*([^\n]+)'
                ],
                'subheadline': [
                    r'(?i)subheadline\s*:\s*"([^"]*)"',
                    r'(?i)subheadline\s*:\s*([^\n]+)'
                ],
                'cta': [
                    r'(?i)cta\s*:\s*"([^"]*)"',
                    r'(?i)cta\s*:\s*([^\n]+)'
                ]
            }
            
            # Try each pattern for each field
            for field, field_patterns in patterns.items():
                for pattern in field_patterns:
                    match = re.search(pattern, response)
                    if match:
                        value = match.group(1).strip()
                        if value:  # Only add non-empty values
                            data[field] = value
                            self.logger.debug(f"Found {field} using pattern {pattern}: {value}")
                            break  # Stop trying patterns for this field once we find a match
            
            # Log the extracted data
            self.logger.debug(f"Extracted data: {data}")
            
            # Validate using Pydantic model
            try:
                cta_response = CTAResponse(**data)
                self.logger.debug(f"Successfully parsed response: {cta_response}")
                return cta_response.dict()
            except Exception as e:
                self.logger.error(f"Validation error: {str(e)}")
                raise NyxAIException(
                    internal_code=7111,
                    message="Invalid response format",
                    detail=f"Response validation failed: {str(e)}"
                )
            
        except NyxAIException:
            raise
        except Exception as e:
            self.logger.error(f"Error parsing response: {str(e)}")
            raise NyxAIException(
                internal_code=7110,
                message="Error parsing CTA response",
                detail=f"7110: {str(e)}"
            )
            
    async def process(self, state: State, config: Dict[str, Any]) -> Dict[str, Any]:
        """Process the state to generate headlines and CTA"""
        print("\n" + "="*80)
        print("🚀 STARTING CTA GENERATOR AGENT")
        print("="*80)
        print("📊 Initial State:")
        for key, value in state.items():
            print(f"  - {key}: {value}")
        print("="*80 + "\n")
        
        self.logger.info("Starting headlines and CTA generation process")
        self.logger.info(f"Current state keys: {list(state.keys())}")
        
        try:
            # Format the prompt with state variables
            prompt_vars = {
                var: state.get(var, "") for var in self.prompt_template.input_variables
            }
            
            # Generate the prompt
            prompt = self.prompt_template.format(**prompt_vars)
            self.logger.debug(f"Generated prompt: {prompt}")
            
            # Get response from LLM
            response = await self._invoke_llm(prompt)
            self.logger.debug(f"Raw LLM response: {response}")
            
            # Parse the response
            result = self._parse_response(response)
            
            # Update state with results
            state["headline"] = result["headline"]
            state["subheadline"] = result["subheadline"]
            state["cta"] = result["cta"]
            
            self.logger.info(f"Headline generated: {result['headline']}")
            self.logger.info(f"Subheadline generated: {result['subheadline']}")
            self.logger.info(f"CTA generated: {result['cta']}")
            
            self.logger.info("Headlines and CTA generated successfully")
            
            print("\n" + "="*80)
            print("✅ COMPLETED CTA GENERATOR AGENT")
            print("="*80)
            print("📊 Final State:")
            for key, value in state.items():
                print(f"  - {key}: {value}")
            print("="*80 + "\n")
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error in headlines and CTA generation: {str(e)}")
            print("\n" + "="*80)
            print("❌ ERROR IN CTA GENERATOR AGENT")
            print("="*80)
            print("📊 Error State:")
            for key, value in state.items():
                print(f"  - {key}: {value}")
            print("="*80 + "\n")
            raise NyxAIException(
                internal_code=7105,
                message="Error generating headlines and CTA",
                detail=f"7105: {str(e)}"
            ) 