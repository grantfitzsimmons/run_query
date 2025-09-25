# run_query
Execute a SQL query on all databases & create automated reports on database statistics.

## Installation

```zsh
python3 -m venv venv
source venv/bin/activate
pip install -r  requirements.txt
```

Create a .env file in the same directory as this script with the following content:

```
DB_HOST=your_host
DB_USER=your_username
DB_PASSWORD=your_password
DB_PORT=3306
SQL_FILE=query.sql (put the name of the query you want to run here)
REGION=northamerica # This can be any string
```

Run the script:

```zsh
python3 runQueryOnAllDatabases.py
```


## Run Remotely

You can extend the `.env` file to enable the execution of `orchestration.py`, which generates comprehensive reports on all databases. This process pulls the latest version of the repository, updates or installs `python3-venv`, activates the virtual environment, installs the required packages, and then runs `runQueryOnAllDatabases.py` on all databases from the `REMOTE_SCRIPT_DIR`. This assumes that the user you are connecting as (defined in the `SERVERS_JSON` .env variable) is a sudoer who does not need to enter a password to proceed.
        

```.env
# For running queries on remote servers
SSH_KEY_PATH=~/.ssh/id_rsa
REMOTE_SCRIPT_DIR=~/run_query
LOCAL_RETRIEVED_DIR=./RetrievedReports
LOG_FILE=orchestration.log

# Define SERVERS as a JSON string. Make sure to escape any quotes properly.
SERVERS_JSON=[{"label":"server-1.example.com","ssh_host":"server-1.example.com","ssh_user":"user1","ssh_key":"~/.ssh/id_rsa"},{"label":"server-2.example.com","ssh_host":"server-2.example.com","ssh_user":"user2","ssh_key":"~/.ssh/id_rsa"},{"label":"server-3.example.com","ssh_host":"server-3.example.com","ssh_user":"user3","ssh_key":"~/.ssh/id_rsa"},{"label":"server-4.example.com","ssh_host":"server-4.example.com","ssh_user":"user4","ssh_key":"~/.ssh/id_rsa"},{"label":"server-5.example.com","ssh_host":"server-5.example.com","ssh_user":"user5","ssh_key":"~/.ssh/id_rsa"},{"label":"server-6.example.com","ssh_host":"server-6.example.com","ssh_user":"user6","ssh_key":"~/.ssh/id_rsa"}]
```

### Automatic Reports

To run this process on a regular basis, you can create a cronjob to run this each Monday. This can be deposited to S3, Google Drive, or similar using [`rclone`](https://github.com/rclone/rclone). Here's an example script that can automate this process (named `run_and_copy.sh` on this system) and log the output:

```bash
#!/usr/bin/env bash
set -euo pipefail

cd /home/ubuntu/run_query
source venv/bin/activate
python3 orchestration.py

rclone copy \
  /home/ubuntu/run_query/RetrievedReports/ \
  "sccvault:Member Files/Hosting Report" \
  --progress \
  --transfers=8 \
  --checkers=16 \
  --drive-chunk-size=64M \
  --drive-upload-cutoff=64M
```

See the `crontab` configuration:

```crontab
# m h  dom mon dow   command
0 3 * * 1 cd /home/ubuntu/run_query && git fetch --prune && for BR in size main; do echo "== Branch: $BR =="; git checkout "$BR" && git pull origin "$BR" && ./run_and_copy.sh; done >> /home/ubuntu/run_query/cron.log 2>&1
```


---

## Asset Usage Reporting

To run daily reports on asset usage, you will need to configure `aws cli` so you can run the `aws s3` commands dynamically.

If new regions are added, we need to extend the `collection_size.sh` and `size.sh` scripts:

```sh
for region in br ca eu il us; do
regions
  bucket="sp-assets-${region}"
```

This assumes the user executing the script has S3 CLI read-only access to all S3 buckets being queried.