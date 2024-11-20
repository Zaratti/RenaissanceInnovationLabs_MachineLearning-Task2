import os
import logging
import json
import openai
import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
from dotenv import load_dotenv
import streamlit as st

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
        # Fetch the database schema
        schema = get_database_schema()
        schema_str = "\n".join(
            f"Table: {table}\n    Columns: {', '.join(columns)}"
            for table, columns in schema.items()
        )

        # Construct the system prompt
        system_message = (
            f"You are a SQL assistant for a SQLite database. Use the following database schema to write valid SQL queries. "
            f"For date-related operations, use strftime('%Y', column_name) to extract the year. "
            f"Only return the SQL:\n{schema_str}"
        )

        # Generate SQL using the xAI client
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

        # Parse the response to extract the SQL
        if hasattr(response, 'choices') and len(response.choices) > 0:
            sql_query = response.choices[0].message.content.strip()

            # Handle SQL formatting
            if sql_query.startswith("```"):
                sql_query = "\n".join(sql_query.split("\n")[1:-1]).strip()

            valid_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE"]
            if any(sql_query.upper().startswith(keyword) for keyword in valid_keywords):
                return sql_query

            return None

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

        # Check if the dataframe has at least two columns for charting
        if dataframe.shape[1] < 2:
            st.error("Insufficient data columns for chart generation. At least two columns are required.")
            return

        # Assuming the first column is 'x' and the second column is 'y'
        x = dataframe.iloc[:, 0]
        y = dataframe.iloc[:, 1]

        # Generate a list of colors for the bars, alternating between blue and red
        colors = ['blue', 'red'] * (len(x) // 2 + 1)
        colors = colors[:len(x)]

        # Create a bar chart
        fig, ax = plt.subplots()
        ax.bar(x, y, color=colors)
        ax.set_xlabel("X-axis Label")
        ax.set_ylabel("Y-axis Label")
        ax.set_title("Chart Title")

        # Display the chart in Streamlit
        st.pyplot(fig)

    except Exception as e:
        logging.error(f"Error generating chart: {str(e)}")
        st.error(f"Error generating chart: {e}")

# Query processing function
def process_query(query, output_format):
    sql_query = generate_sql(query)
    if not sql_query:
        st.error("Failed to generate a valid SQL query. Please rephrase your query.")
        st.session_state.show_examples = True  # Show examples when query fails
        return False  # Return False to indicate failure

    st.session_state.show_examples = False  # Hide examples when query succeeds

    try:
        with model.connect() as conn:
            result = pd.read_sql(sql_query, conn)

        if output_format == "text":
            st.text(result.to_string(index=False))
        elif output_format == "table":
            st.dataframe(result)
        elif output_format == "chart":
            generate_chart(result)
        
        return True  # Return True to indicate success

    except Exception as e:
        logging.error(f"Error processing query: {str(e)}")
        st.error(f"Error processing query: {str(e)}")
        return False

# Streamlit app layout
# Add custom CSS and an image
st.markdown(
    """
    <style>
        .main {
            background-color: #f0f8ff; /* Light blue background */
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 20px;
        }
        .header img {
            width: 150px;
            margin-bottom: 10px;
        }
        .header h1 {
            font-family: Arial, sans-serif;
            font-size: 2.5rem;
            color: #333;
        }
        .header p {
            font-family: Arial, sans-serif;
            font-size: 1.2rem;
            color: #666;
        }
    </style>
    <div class="header">
        <img src="https://cdn-uploads.huggingface.co/production/uploads/637b0075806b18943e4ba357/_5rdIQZwyaUFb84xKW_AV.png" alt="Text2SQL Image">
        <h1>Natural Language to SQL App</h1>
        <p>Query your database using plain English.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Main app content
with st.container():
    query = st.text_input("Enter your natural language query:", placeholder="Enter your query here...")
    output_format = st.selectbox("Select output format:", ["text", "table", "chart"])

# Show dynamic examples only when needed
if st.session_state.get("show_examples", False):
    st.sidebar.subheader("Example Queries For Chart")
    st.sidebar.write("""
    - Show the total sales for each product category.
    - List the last five registered users.
    - Show the count of users registered in each year.
    - Show the last ten orders in each month.
    """)

# Button to process the query
if st.button("Process Query"):
    if not query:
        st.error("Please enter a query.")
        st.session_state["show_examples"] = True  # Show examples if the query is empty or invalid
    else:
        success = process_query(query, output_format)
        st.session_state["show_examples"] = not success  # Hide examples if the query was successful