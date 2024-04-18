import os 
from dotenv import load_dotenv
from flask import Flask, request
from flask_cors import CORS

import pandas as pd 
import pandas as pd
import sqlite3

from langchain_openai import AzureChatOpenAI
from langchain.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

import sqlite3
import os
import pandas as pd

load_dotenv()

db_name = "allotrac.db"

app = Flask(__name__)
CORS(app)
cors = CORS(app, resource={
    r"/*":{
        "origins":"*"
    }
})

llm = AzureChatOpenAI(
        azure_deployment="gpt-4",
        model_name="gpt-4",
        azure_endpoint=os.environ.get("API_ENDPOINT"),
        openai_api_version=os.environ.get("API_VERSION"),
        openai_api_key=os.environ.get("API_KEY"),
        temperature=0
    )

chain_template = """
    {past_history}
    
    {history}

    based on above history, I have below questions.

    Question: {question}
`
    Answer: Explain these result data in human readable format and generate human readable summary. The summary should be in bullet points as far as possible. 
    Don't mention the datasource. 
    """

chain_prompt = PromptTemplate.from_template(chain_template)
llm_chain = LLMChain(prompt=chain_prompt, llm=llm)

# def load_data_to_db():
    
#     base_path = "/Users/blinkganesh/personal/hackathon2024/csv-dataset"
    
#     for csv_path in os.listdir(base_path):
#         if csv_path.endswith('.csv'):
#             table_name = csv_path.split('.')[0]

#             df = pd.read_csv(f'{base_path}/{csv_path}')
#             df.to_sql(table_name, conn, if_exists='replace', index=False)


def create_db_chain(table_list):
    connection_uri = f"sqlite:///{db_name}"

    db = SQLDatabase.from_uri(connection_uri, include_tables=table_list, sample_rows_in_table_info=3)

    db_chain = SQLDatabaseChain.from_llm(llm, db)

    db_chain.return_sql = True
    db_chain.return_direct = True
    
    return db_chain


def generate_query(query, db_chain):
    query_gen_tpl = """You are an expert sql query generator who understands the question in english and convert to sql query strictly based on the context. 
        Please be extra careful while handling ambiguous fields and tables while joining. 
        
        The table description is as follows:
            customer - Example Allotrac Site Customers
            delivery_type - Example delivery types
            fleet - The Vehicle fleets for the example site
            item - The list of products that are transported by the example customer (this is the catalogue, not the instantiated instances of items on a delivery)
            location - The list of locations stored against allotrac contacts
            state - Australian States
            suburb - Australian Suburbs
            truck - The vehicles attached to the Allotrac site
            truck_home_location_data - A mapping of vehicles to locations where the trucks are parked overnight
            truckclass - The various varieties of vehicles tracked in Allotrac
            truckhistory - The GPS data of all vehicles in Allotrac during. Please ignore MaximumSpeed field for all queries. 
            msjob_activities - All job activities
            msjob_activity_types - The lookup for the activity type mapping
            msjob_history - All status changes for jobs
            msjob_status - The lookup for the job statuses
            msjob_pod - All proof of delivery documents for jobs
            msjob_project - Projects (which can join a collection of jobs under a single instance)
            msjobcustomer - Each line here represents an individual job done in Allotrac, this is the core table for workflow
            msjobcusttoitems - Each line here maps an instantiated item to an instantiated job to allow for multiple items per job
            msjobitems - The instantiated items for jobs
            msprojectitems - The instantiated items for projects
            mstrucktocust - The mapping from instantiated jobs to vehicles in the system
        The table description is very important while generating sql query. Be as specific as possible while generating the query.
        Human: {question}
        Assistant: 
        """
    r = db_chain.invoke(query_gen_tpl.replace("{question}", query))
    
    return r["result"]

def summarize(query, sql, db_result, past_history):
    result = llm_chain.invoke(
        {
            "history": f"{query} RESULT QUERY IS : \n {sql} \n RETURN FROM DB: \n {db_result}",
            "question": query, 
            "past_history": past_history
        }
    )

    return result

base_path = "/Users/blinkganesh/personal/hackathon2024/csv-dataset"
table_list = []

for csv_path in os.listdir(base_path):
    if csv_path.endswith('.csv'):
        table_name = csv_path.split('.')[0]
        table_list.append(table_name)

db_chain = create_db_chain(table_list)

@app.route('/', methods=['POST'])
def run_bot():
    request_json = request.json
    
    prompt = request_json["prompt"]
    history = request_json["history"]
    
    past_history = ""
    if len(history) > 4:
        past_history = past_history[-4:]
    human_prompt = [ data['text'] for idx, data in enumerate(history) if idx %2 == 0 ]
    bot_result = [ data['text'] for idx, data in enumerate(history) if idx %2 == 1]
    # for (h_text, b_text) in zip(human_prompt, bot_result):
    #     past_history += f"Human Query: \n {h_text} \nResponse: \n {b_text}\n"
        
    print("Generating query")
    sql_response = generate_query(prompt, db_chain)
    print(sql_response)
    
    conn = sqlite3.connect(db_name)
    
    print("Getting result")
    db_result = conn.execute(sql_response).fetchall()
    print(db_result)
    
    print("Generating summary")
    summary = summarize(prompt, sql_response, db_result, past_history)
    # print(summary)
    summary = summary["text"] + f"""

    Db-result: {db_result}
    """
    
    return summary


if __name__ == '__main__':
    # load_data_to_db()
    app.run(host='0.0.0.0', port=8080) 