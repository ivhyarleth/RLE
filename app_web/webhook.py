from flask import request, jsonify, Blueprint
from .utils import get_response_or_cache  # Tu función mejorada
import json
import os

webhook_routes = Blueprint('webhook_routes', __name__)

@webhook_routes.route('/')
def home():
    return 'All is well...'

@webhook_routes.route('/rabbit', methods=['POST'])
def send_rabbit_recommendation():
    # Cargar configuración
    with open('config.json', 'r', encoding='utf-8') as file:
        config = json.load(file)

    # Obtener la query del body
    req_data = request.get_json()
    query = req_data.get('query', "")

    # Parámetros de BigQuery (ajusta si tu config.json tiene otros nombres de clave)
    project_id = config['PROJECT_ID']
    dataset_id = config['DATASET_ID']
    table_id = config['TABLE_ID']

    # Obtener respuesta (de cache o del LLM)
    response = get_response_or_cache(project_id, dataset_id, table_id, query)

    return jsonify({
        "response": response
    })