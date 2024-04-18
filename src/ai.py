from openai import AzureOpenAI

import os 

from dotenv import load_dotenv

load_dotenv()

client = AzureOpenAI(
  azure_endpoint = os.environ.get("API_ENDPOINT"), 
  api_key = os.environ.get("API_KEY"),  
  api_version = os.environ.get("API_VERSION")
)

