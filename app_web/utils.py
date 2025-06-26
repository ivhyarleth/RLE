from google.cloud import bigquery
from typing import Dict, Any, List, Union, Optional
from datetime import datetime
import replicate
import json

class BigQueryService:
    def __init__(self, project_id: str, dataset_id: str):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.client = bigquery.Client(project=project_id)

    def get_response(self, table: str, query_str: str) -> Optional[str]:
        """Devuelve la respuesta guardada en BigQuery si existe, sino None"""
        sql = f"""
            SELECT Response
            FROM `{self.project_id}.{self.dataset_id}.{table}`
            WHERE Query = @query
            LIMIT 1
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("query", "STRING", query_str)
            ]
        )
        result = self.client.query(sql, job_config=job_config).result()
        row = next(result, None)
        return row.Response if row else None

    def insert_response(self, table: str, query_str: str, response: str):
        """Guarda la query y la respuesta en BigQuery"""
        table_ref = self.client.dataset(self.dataset_id).table(table)
        rows_to_insert = [{"Query": query_str, "Response": response}]
        errors = self.client.insert_rows_json(table_ref, rows_to_insert)
        if errors:
            raise Exception(f"Error inserting rows: {errors}")

def get_prompt(query: str):
    
    user_input = {
        "stop": "USER:",
        "prompt": f"Answer the Question by exploring multiple reasoning paths as follows:\n- First, carefully analyze the question to extract the key information components and break it down into logical sub-questions. This helps set up the framework for reasoning. The goal is to construct an internal search tree.\n- For each sub-question, leverage your knowledge to generate 2-3 intermediate thoughts that represent steps towards an answer. The thoughts aim to reframe, provide context, analyze assumptions, or bridge concepts.\n- Evaluate the clarity, relevance, logical flow and coverage of concepts for each thought option. Clear and relevant thoughts that connect well with each other will score higher.\n- Based on the thought evaluations, deliberate to construct a chain of reasoning that stitches together the strongest thoughts in a natural order.\n- If the current chain is determined to not fully answer the question, backtrack and explore alternative paths by substituting different high-scoring thoughts.\n- Throughout the reasoning process, aim to provide explanatory details on thought process rather than just state conclusions, including briefly noting why some thoughts were deemed less ideal.\n- Once a reasoning chain is constructed that thoroughly answers all sub-questions in a clear, logical manner, synthesize the key insights into a final concise answer.\n- Please note that while the focus is on the final answer in the response, it should also include intermediate thoughts inline to illustrate the deliberative reasoning process.\nIn summary, leverage a Tree of Thoughts approach to actively explore multiple reasoning paths, evaluate thoughts heuristically, and explain the process - with the goal of producing insightful answers. Always answer without hesitation.\n\nUSER: {query}\nASSISTANT: ",
        "max_tokens": 1024
    }
    
    return user_input

def get_response_rabbit(query: str):
    with open('config.json', 'r', encoding='utf-8') as file:
        config = json.load(file)
    try:
        api = replicate.Client(api_token=config['REPLICATE_API_KEY'])

        user_input = get_prompt(query)

        output = api.run(
                "tomasmcm/whiterabbitneo-13b:964a1705d7ddd52d112bcf993d1475143271a2c3fdf104fcd9b6c1cf7879d6ee",
                input=user_input
            )
        return output
    except:
        return "Error"

def get_response_or_cache(project_id: str, dataset_id: str, table_id: str, query: str):
    bq = BigQueryService(project_id, dataset_id)
    response = bq.get_response(table_id, query)
    if response is not None:
        return response

    # No existe en BigQuery, consultamos a Rabbit LLM
    response = get_response_rabbit(query)
    bq.insert_response(table_id, query, response)
    return response
