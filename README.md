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


## Run on remote servers

You can extend the `.env` file to run the `orchestration.py`.

```.env
# For running queries on remote servers
SSH_KEY_PATH=~/.ssh/id_rsa
REMOTE_SCRIPT_DIR=~/run_query
LOCAL_RETRIEVED_DIR=./RetrievedReports
LOG_FILE=orchestration.log

# Define SERVERS as a JSON string. Make sure to escape any quotes properly.
SERVERS_JSON=[{"label":"server-1.example.com","ssh_host":"server-1.example.com","ssh_user":"user1","ssh_key":"~/.ssh/id_rsa"},{"label":"server-2.example.com","ssh_host":"server-2.example.com","ssh_user":"user2","ssh_key":"~/.ssh/id_rsa"},{"label":"server-3.example.com","ssh_host":"server-3.example.com","ssh_user":"user3","ssh_key":"~/.ssh/id_rsa"},{"label":"server-4.example.com","ssh_host":"server-4.example.com","ssh_user":"user4","ssh_key":"~/.ssh/id_rsa"},{"label":"server-5.example.com","ssh_host":"server-5.example.com","ssh_user":"user5","ssh_key":"~/.ssh/id_rsa"},{"label":"server-6.example.com","ssh_host":"server-6.example.com","ssh_user":"user6","ssh_key":"~/.ssh/id_rsa"}]
```