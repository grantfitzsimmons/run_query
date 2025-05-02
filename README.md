# run_query
Execute a SQL query on all databases

## Installation

```zsh
python3 -m venv venv
source venv/bin/activate
pip install requirements.txt
```

Create a .env file in the same directory as this script with the following content:

```
DB_HOST=your_host
DB_USER=your_username
DB_PASSWORD=your_password
DB_PORT=3306
SQL_FILE=query.sql (put the name of the query you want to run here)
```

Run the script:

```zsh
python3 runQueryOnAllDatabases.py
```