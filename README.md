# RenaissanceInnovationLabs_MachineLearning-Task2
### Natural Language Query Interface for Database Access.
This application demonstrates how to convert natural language queries into SQL using the xAI API, runs the SQL on a connected database and visualize the results in various formats (text, table, and chart). The system uses a Flask web application to handle user input, generate SQL queries, execute them against a SQLite database, and return formatted responses.

## Installation

#### 1. Clone the repository:
- git clone [Natural Language Query for Database Access Repository](https://github.com/Zaratti/RenaissanceInnovationLabs_MachineLearning-Task2.git)
- when you have done that, use _cd nLQDatabaseAccess_ to get into the folder.

- Set up your IDE Integrated Developement Environment(I used VScode).
     - Read the [Project Documentation ML (Project 2)](https://github.com/Zaratti/RenaissanceInnovationLabs_MachineLearning-Task2/blob/main/Project%20Documentation%20ML%20(Project%202).ipynb), to understand this project goal.
     - Make sure that you have the requirements.txt(_pip install -r requirements.txt_) in your local folder, this will enable you manage dependencies that are required for the project.
     - Set up .gitignore to also enable you handle large files, confirm you have the venv/ and .env/ inside the .gitignore file. 

### Challenges Documentation(Schema and SQL Refining)
- After setting up the necessary library's in the Flask app: (I used VS Code). I loaded the environment variables and set up connection to the database using their supported parameters.
    - **Natural Language to SQL**: The interface accepts natural language input, send that natural language query to xA.I, lets xA.I know it is the system and how to generate SQL queries from natural language inputs using a schema that xAI's model work with to genrate SQL for the database.
    - **Dynamic Schema Usage**: Used json, to set a schema that clearly outlines the column names, data type and description structure of the database to enhance SQL generation accuracy.
    - **Database Integration**: Connects to a SQLite database to execute generated SQL queries from xA.I.
    - **Error Handling**: I used try and exceptions to return detailed error messages for invalid inputs or unsupported formats, and handle such errors.
    - **Logging**: For easier debugging processes, I used logging within the exceptions for comprehensive request and error logginh.
    - **Result Formats**: Output results are in:
        - **Text**: This shows plain text representation of query results.
        - **Table**: This shows HTML table for structured data.
        - **Chart**: This shows Visual bar charts based on query results.

### Usage/Setup
- Clone the Repository
- Install Dependencies
- Configure Environment Variables
- Prepare the Database
- Run the Application
- Test the API using Postman to test the query endpoint and visualize your result.


## Notes
- Ensure the xAI API key(or whatever model you decide to use) has sufficient quota to handle requests, this will help you handle RateLimitErrors.
- Update the database file(I used sqlite, your database could be different) and schema(that is, an outlined description of the structure of your connected database) as needed to match your application.

## Example Queries
- Text:
 ```{
        "query": "List the last five users",
        "format": "text"
    }
```

- Table:
 ```{
    "query": "Show the number of users who signed up each year",
    "format": "table"
    }
 ```

- Chart:
 ```{
    "query": "Visualize the number of users who signed up each year",
    "format": "chart"
    }
 ```
