from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task, before_kickoff, after_kickoff
import os
import json
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from .tools.dates import CurrentDateTool
import asyncio

load_dotenv()

class BrandMapping(BaseModel):
	brand_name: str = Field(...,description="Name of Brand")
	website: str = Field(...,description="Website of Brand")
	brand_description: str = Field(...,description="Description of Brand")
	product_name: Optional[str] = Field(...,description="Product of Brand")
	product_description: Optional[str] = Field(...,description="Description of Product")
	industry: str = Field(...,description="Classified Industry Type")
	
class TargetGroup(BaseModel):
	age: str = Field(...,description="Age Group for Brand")
	gender: str = Field(...,description="Gender for Brand")
	location: str = Field(...,description="Location for Brand")
	interests: List[str] = Field(...,description="Interests related to brand")
	psychographic_traits: List[str] = Field(...,description="Traits related to Brand")

class RecommendedChannel(BaseModel):
	channel_name: List[str] = Field(...,description="List of Channels")

class Dates(BaseModel):
	start_date: str = Field(...,description="Start Date of Campaign")
	end_date: str = Field(...,description="End Date of Campaign")

class Budget(BaseModel):
	total_budget: float = Field(...,description="Total Budget for Campaign")
	allocation: Dict[str,float] = Field(...,description="Budget Split across Recommended channels")

class CampaignName(BaseModel):
	campaign_name: str = Field(...,description="Campaign Name")

@CrewBase
class CampaignSetup():
	"""Campaign Setup And Planning Crew"""

	def __init__(self):
		self.inputs = None
		self.llm = LLM(
            model="openai/gpt-4o",  
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.7
        )
		self.agents_config = os.getenv('AGENT_CONFIG')
		self.tasks_config = os.getenv('TASK_CONFIG')

	@before_kickoff
	def before_kickoff_function(self, inputs):
		print(f"Before kickoff function with inputs: {inputs}")
		self.inputs = inputs
		return inputs 
    
	@after_kickoff
	def process_results(self, result):
		print(f"After kickoff function with result: {result}")
		
		return result
	
	@agent
	def brand_mapping_agent(self) -> Agent:
		"""Agent to map brand names to their respective categories"""
		return Agent(
			config=self.agents_config['brand_mapping_agent'],
			llm = self.llm,
			verbose= True
		)
	
	@task
	def brand_mapping_classification_task(self) -> Task:
		return Task(
			config=self.tasks_config['brand_mapping_classification_task'],
			agent=self.brand_mapping_agent(),
			output_json=BrandMapping
		)

	@agent
	def audience_identification_agent(self) -> Agent:
		"""Agent to identify the target audience for the campaign"""
		return Agent(
			config=self.agents_config['audience_identification_agent'],
			llm = self.llm,
			verbose= True
		)
	
	@task
	def audience_identification_task(self) -> Task:
		return Task(
			config=self.tasks_config['audience_identification_task'],
			agent=self.audience_identification_agent(),
			context = [self.brand_mapping_classification_task()],
			output_json=TargetGroup			
		)

	@agent
	def channel_recommendation_agent(self) -> Agent:
		"""Agent to recommend channels for the campaign"""
		return Agent(
			config=self.agents_config['channel_recommendation_agent'],
			llm = self.llm,
			verbose= True
			)
	
	@task
	def channel_recommendation_task(self) -> Task:
		return Task(
			config=self.tasks_config['channel_recommendation_task'],
			agent=self.channel_recommendation_agent(),
			context = [self.audience_identification_task(),self.brand_mapping_classification_task()],
			output_json=RecommendedChannel,
			
		)
	
	@agent
	def schedule_recommendation_agent(self):
		"""Agent to recommend schedule for the campaign"""
		return Agent(
			config=self.agents_config['schedule_recommendation_agent'],
			llm = self.llm,
			verbose= True,
			tools = [CurrentDateTool()]
			)
	
	@task
	def schedule_recommendation_task(self) -> Task:
		return Task(
			config=self.tasks_config['schedule_recommendation_task'],
			agent=self.schedule_recommendation_agent(),
			context = [self.channel_recommendation_task(),self.audience_identification_task(),self.brand_mapping_classification_task()],
			output_json=Dates
		)
	
	@agent
	def budget_allocation_agent(self):
		"""Agent to recommend budget for the campaign"""
		return Agent(
			config=self.agents_config['budget_allocation_agent'],
			llm = self.llm,
			verbose= True
			)
	
	@task
	def budget_allocation_task(self) -> Task:
		return Task(
			config=self.tasks_config['budget_allocation_task'],
			agent=self.budget_allocation_agent(),
			context = [self.schedule_recommendation_task(),self.channel_recommendation_task(),self.audience_identification_task(),self.brand_mapping_classification_task()],
			output_json=Budget,
			human_input=True
			)

	@agent
	def campaign_name_recommendation_agent(self):
		"""Agent to generate campaign names"""
		return Agent(
			config=self.agents_config['campaign_name_recommendation_agent'],
			llm = self.llm,
			verbose= True			
			)
	
	@task
	def campaign_name_recommendation_task(self) -> Task:
		return Task(
			config=self.tasks_config['campaign_name_recommendation_task'],
			agent=self.campaign_name_recommendation_agent(),
			context = [self.schedule_recommendation_task(),self.channel_recommendation_task(),self.audience_identification_task(),self.brand_mapping_classification_task()],
			output_json=CampaignName
			)

	@crew
	def crew(self) -> Crew:
		"""Creation of CampaignPlanningCrew"""
		return Crew(
			agents=self.agents,
			tasks=self.tasks,
			process=Process.sequential,
			verbose=True,
			planner=True,
			memory=True
		)








