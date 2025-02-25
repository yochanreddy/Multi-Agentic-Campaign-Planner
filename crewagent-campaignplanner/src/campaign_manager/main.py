#!/usr/bin/env python

from pydantic import BaseModel
from typing import Dict,List
import json
from crewai.flow import Flow, listen, start
from .crews.campaign_setup_crew.campaign_setup_crew import CampaignSetup

from dotenv import load_dotenv
import os
import warnings
from chromadb import Client, Settings
import chromadb
from datetime import datetime
import redis 
import json
import asyncio

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")
load_dotenv()



class CampaignPlannerState(BaseModel):
    outcome: Dict[str,str]= {}

class CampaignPlannerFlow(Flow[CampaignPlannerState]):

    @start()
    async def campaign_complete_initialization(self):
        print("Setting up the campaign")
        
        with open(os.getenv('INPUT_FILE'),'r') as f:
            inputs = json.load(f)
        print(inputs)

        setup_crew = CampaignSetup()
        
        outcome = setup_crew.crew().kickoff(inputs=inputs)
        campaign_setup_results = {}
        for task in range(len(outcome.tasks_output)):
            task_name = outcome.tasks_output[task].name  
            campaign_setup_results[task_name] = outcome.tasks_output[task].json_dict
        
        print(campaign_setup_results)
        self.state.outcome = campaign_setup_results
    
    @listen(campaign_complete_initialization)
    def save_outcome_to_file(self):
        print("Saving outcome to file")
        dir_path = os.getenv('OUTPUT_FILE')
        os.makedirs(dir_path, exist_ok=True)
        fp = os.path.join(dir_path, "campaign_setup.json")
        with open(fp, "w") as json_file:
           json.dump(self.state.outcome, json_file, indent=4)
    
    @listen(save_outcome_to_file)
    def store_in_chromadb(self):
        print("Storing campaign setup data in ChromaDB")
        try:
            # Initialize ChromaDB client
            chroma_client = chromadb.Client(Settings(
                persist_directory="chroma_db",
                is_persistent=True
            ))

            # Create or get collection
            collection = chroma_client.get_or_create_collection(
                name="campaign_setups",
                metadata={"description": "Campaign setup configurations"}
            )

            # Convert the JSON data to strings for storage
            documents = [json.dumps(self.state.outcome)]
            ids = [f"campaign_setup_{len(collection.get()['ids']) + 1}"]
            metadatas = [{
                "brand_name": self.state.outcome["brand_mapping_classification_task"]["brand_name"],
                "timestamp": str(datetime.now())
            }]

            # Add the data to ChromaDB
            collection.add(
                documents=documents,
                ids=ids,
                metadatas=metadatas
            )
            print(f"Successfully stored campaign setup data with ID: {ids[0]}")
            
        except Exception as e:
            print(f"Error storing data in ChromaDB: {str(e)}")


def kickoff():
    campaign_planner = CampaignPlannerFlow()
    campaign_planner.kickoff()


def plot():
    campaign_planner = CampaignPlannerFlow()
    campaign_planner.plot()


if __name__ == "__main__":
    kickoff()

#1)data from crew , required to be validate thereby creating validator crew and utilize
#2)if any task or agent fails, crew should be efficiently terminated and fallback should
# be executed to generate the error
#3) store error handling across the crew and tasks to track errors and their causes. store detailed error from task agent and how it occurs(upstream,downstram,)
# Implement lstm for memory and store in chromadb
# Modify input struct to prod level
# Check out memory attribute, validation checks for agent crew task
# Hierarchical process and manager implementation
# Each entry for each campaign with updated timestamp for same brand to be recorded in this style
# Focus on llm tool implementation only, historical data use dummy functions
# Implement campaign objective agent in campaign setup crew
# Previous:
# Error handling, fallback, validation crew

# mom
#  we need to validate the data from the crew
# should we abort the crew if the data is not valid? what will be fallback scenario?
# how frequently we need to store the data in the database? do we want to all info for given campaign id or just the latest one?
# do we store each and every interaction of user or final outcome?
# data is inappropriate.
# how to validate the time series data?
# explanation and integration in terms of UI and interaction.
