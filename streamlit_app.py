import os
import logging
import json
import openai
import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
from dotenv import load_dotenv
import streamlit as st
import base64
from pathlib import Path

# Load environment variables
load_dotenv()
XAI_API_KEY = os.getenv("XAI_API_KEY")

if not XAI_API_KEY:
    st.error("XAI_API_KEY is not set in the environment variables.")
    st.stop()

# Initialize the xAI client
client = openai.OpenAI(api_key=XAI_API_KEY, base_url="https://api.x.ai/v1")

# Database and schema setup
DATABASE_FILE = "example_database.sqlite"
SCHEMA_FILE_PATH = "schema.json"

# Function to encode image to Base64
def img_to_bytes(img_path):
    img_bytes = Path(img_path).read_bytes()
    encoded = base64.b64encode(img_bytes).decode()
    return encoded

# Function to create an HTML img tag with the Base64-encoded image
def img_to_html(img_path):
    img_html = "<img src='data:image/png;base64,{}' class='img-fluid' style='display: block; width: 25%; margin: 0 auto;'>".format(
        img_to_bytes(img_path)
    )
    return img_html

# Load schema
def load_schema(schema_file_path):
    try:
        with open(schema_file_path, 'r') as schema_file:
            schema = json.load(schema_file)
        return schema
    except Exception as e:
        st.error(f"Error loading schema: {e}")
        return {}

schema = load_schema(SCHEMA_FILE_PATH)

# Initialize database connection
model = create_engine(f"sqlite:///{DATABASE_FILE}")

# SQL query generation (function for xAI)
def generate_sql(natural_language_query):
    try:
        schema = get_database_schema()
        schema_str = "\n".join(
            f"Table: {table}\n    Columns: {', '.join(columns)}"
            for table, columns in schema.items()
        )

        system_message = (
            f"You are a SQL assistant for a SQLite database. Use the following database schema to write valid SQL queries. "
            f"For date-related operations, use strftime('%Y', column_name) to extract the year. "
            f"Only return the SQL:\n{schema_str}"
        )

        response = client.chat.completions.create(
            model="grok-beta",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": natural_language_query}
            ],
            stream=False,
            max_tokens=150,
            temperature=0
        )

        if hasattr(response, 'choices') and len(response.choices) > 0:
            sql_query = response.choices[0].message.content.strip()

            if sql_query.startswith("```"):
                sql_query = "\n".join(sql_query.split("\n")[1:-1]).strip()

            valid_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE"]
            if any(sql_query.upper().startswith(keyword) for keyword in valid_keywords):
                return sql_query

        return None

    except Exception as e:
        logging.error(f"Error in SQL generation: {str(e)}")
        return None

def get_database_schema():
    schema = {}
    try:
        with model.connect() as conn:
            tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)
            for table in tables['name']:
                columns = pd.read_sql(f"PRAGMA table_info({table});", conn)
                schema[table] = columns['name'].tolist()
    except Exception as e:
        logging.error(f"Error fetching database schema: {str(e)}")
    return schema

# Chart generation
def generate_chart(dataframe):
    try:
        if dataframe.empty:
            st.error("No data available to generate a chart.")
            return

        if dataframe.shape[1] < 2:
            st.error("Insufficient data columns for chart generation. At least two columns are required.")
            return

        x = dataframe.iloc[:, 0]
        y = dataframe.iloc[:, 1]

        colors = ['blue', 'red'] * (len(x) // 2 + 1)
        colors = colors[:len(x)]

        fig, ax = plt.subplots()
        ax.bar(x, y, color=colors)
        ax.set_xlabel("X-axis Label")
        ax.set_ylabel("Y-axis Label")
        ax.set_title("Chart Title")

        st.pyplot(fig)

    except Exception as e:
        logging.error(f"Error generating chart: {str(e)}")
        st.error(f"Error generating chart: {e}")

# Query processing function
def process_query(query, output_format):
    sql_query = generate_sql(query)
    if not sql_query:
        st.error("Failed to generate a valid SQL query. Please rephrase your query.")
        st.session_state.show_examples = True
        return False

    st.session_state.show_examples = False

    try:
        with model.connect() as conn:
            result = pd.read_sql(sql_query, conn)

        if output_format == "text":
            st.text(result.to_string(index=False))
        elif output_format == "table":
            st.dataframe(result)
        elif output_format == "chart":
            generate_chart(result)

        # Add CSS-based download buttons
        st.markdown(
            """
            <style>
                .download-buttons-container {
                    display: flex;
                    justify-content: left;
                    gap: 15px;
                    margin-top: 10px;
                }
                .download-button {
                    background-color: #f0f8ff;
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    padding: 5px 10px;
                    text-align: center;
                    font-family: Arial, sans-serif;
                    font-size: 14px;
                    text-decoration: none;
                    color: black;
                }
                .download-button:hover {
                    background-color: #d0e8ff;
                }
            </style>
            """,
            unsafe_allow_html=True,
        )

        csv_download_link = f"""
        <a href="data:text/csv;base64,{base64.b64encode(result.to_csv(index=False).encode('utf-8')).decode()}" download="query_result.csv" class="download-button">
            Download as CSV
        </a>
        """

        json_download_link = f"""
        <a href="data:application/json;base64,{base64.b64encode(result.to_json(orient="records", lines=True).encode('utf-8')).decode()}" download="query_result.json" class="download-button">
            Download as JSON
        </a>
        """

        st.markdown(
            f"""
            <div class="download-buttons-container">
                {csv_download_link}
                {json_download_link}</div>
            """,
            unsafe_allow_html=True,
        )

        return True

    except Exception as e:
        logging.error(f"Error processing query: {str(e)}")
        st.error(f"Error processing query: {str(e)}")
        return False

# Streamlit app layout
st.markdown(
    """
    <style>
        .header {
            text-align: center;
            margin-bottom: 20px;
        }
        .header h1 {
            font-family: Arial, sans-serif;
            font-size: 2.5rem;
            color: #333;
        }
        .header p {
            font-size: 1.2rem;
            color: #666;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Add the header image and text
st.markdown(
    """
    <div class="header">
        {}
        <h1>Natural Language to SQL App</h1>
        <p>Query your database using plain English.</p>
    </div>
    """.format(img_to_html("nLDatabaseAccessImg.webp")),
    unsafe_allow_html=True,
)

with st.container():
    query = st.text_input("Enter your natural language query:", placeholder="Enter your query here...")
    output_format = st.selectbox("Select output format:", ["text", "table", "chart"])

if st.session_state.get("show_examples", False):
    st.sidebar.subheader("Example Queries For Chart")
    st.sidebar.write("""
    - Show the total sales for each product category.
    - List the last five registered users.
    - Show the count of users registered in each year.
    - Show the last ten orders in each month.
    """)

if st.button("Process Query"):
    if not query:
        st.error("Please enter a query.")
        st.session_state["show_examples"] = True
    else:
        success = process_query(query, output_format)
        st.session_state["show_examples"] = not success
