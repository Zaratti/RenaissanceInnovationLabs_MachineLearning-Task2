# Import necessary libraries/modules
from flask import Flask, request, jsonify, send_file
import sqlalchemy
import openai  # for GPT-4 integration
import os
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
import pandas as pd
import premsql
from dotenv import load_dotenv  # Import load_dotenv from python-
from premsql.pipelines import SimpleText2SQLAgent
from premsql.generators import Text2SQLGeneratorHF
from premsql.executors import SQLiteExecutor

app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

# Connect to the SQLite database
DATABASE_FILE = "example_database.sqlite"
model = create_engine(f"sqlite:///{DATABASE_FILE}")

# Route to handle admin queries
@app.route('/', methods=['GET'])
def home():
    return "Welcome to the Natural Language Query Database API. Use /query to post your natural language queries."


@app.route('/query', methods=['POST'])
def process_query():
    data = request.json
    query_text = data.get('query')
    output_format = data.get('format', 'text')

    # Step 1: Convert natural language to SQL using OpenAI
    sql_query = generate_sql(query_text)

    # Step 2: Execute SQL query
    with model.connect() as conn:
        result = pd.read_sql(sql_query, conn)

    # Step 3: Process output format
    if output_format == 'text':
        return jsonify(result.to_string())
    elif output_format == 'table':
        return result.to_html()
    elif output_format == 'chart':
        chart = generate_chart(result)
        return send_file(chart, mimetype='image/png')

def generate_sql(natural_language_query):
    #Use PremAI API to convert natural language to SQL
    agent = SimpleText2SQLAgent(
        dsn_or_db_path=DATABASE_FILE,
        generator=Text2SQLGeneratorHF(
        model_or_name_or_path="premai-io/prem-1B-SQL",
        experiment_name="simple_pipeline",
        device="cuda:0",
        type="test"
        ),
    )
    
    response = agent.query(natural_language_query)
    response["table"]

def generate_chart(result_df):
    # Generate a bar chart using matplotlib
    plt.figure(figsize=(8, 6))
    result_df.plot(kind='bar')
    plt.savefig('chart.png')
    return 'chart.png'

if __name__ == '__main__':
    app.run(debug=True)
