import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import csv
from datetime import datetime # Import datetime

# Load environment variables from the .env file
load_dotenv()

# Database connection parameters
DB_HOST     = os.getenv('DB_HOST')
DB_USER     = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_PORT    = os.getenv('DB_PORT', 3306)
SQL_FILE = os.getenv('SQL_FILE', 'query.sql')
REGION = os.getenv('REGION', DB_HOST)

# Output directory (relative to where the script is run on the remote server)
# This should align with the REMOTE_SCRIPT_DIR and potential OUTPUT_DIR setting
# used by your orchestrator if you intend to retrieve these files.
# Let's assume an 'Output' subdirectory within the script directory.
OUTPUT_DIR = "./Output"
os.makedirs(OUTPUT_DIR, exist_ok=True) # Ensure the output directory exists

def read_query_from_file(file_path):
    """Read the SQL query from the specified file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f: # Specify encoding
            return f.read()
    except FileNotFoundError:
        print(f"Error: SQL file not found at '{file_path}'")
        return None # Return None if file not found
    except Exception as e:
        print(f"Error reading SQL file '{file_path}': {e}")
        return None

def execute_query_on_all_databases(sql_query, output_csv_path): # Pass full output path
    if sql_query is None:
        print("SQL query not loaded. Exiting.")
        return

    # ——— truncate or remove any existing export file ———
    # This now removes the specific CSV file for this run
    if os.path.exists(output_csv_path):
        print(f"Removing existing output file: {output_csv_path}")
        os.remove(output_csv_path)

    connection = None
    try:
        print(f"Connecting to database: {DB_HOST}:{DB_PORT} as {DB_USER}")
        connection = mysql.connector.connect(
            host     = DB_HOST,
            user     = DB_USER,
            password = DB_PASSWORD,
            port     = DB_PORT
        )
        if not connection.is_connected():
            print("Failed to connect to the server.")
            return

        cursor = connection.cursor()
        # Exclude system databases
        cursor.execute("SHOW DATABASES WHERE `Database` NOT IN ('information_schema', 'performance_schema', 'mysql', 'sys', 'innodb');")
        databases = [row[0] for row in cursor.fetchall()]

        if not databases:
            print("No user databases found on this server.")
            return

        print(f"Found {len(databases)} user databases.")

        # Track whether we've written the header yet
        header_written = False

        # Open the CSV file for writing (will create if it doesn't exist after os.remove)
        with open(output_csv_path, mode='w', newline='', encoding='utf-8') as csvfile: # Changed to 'w' as we removed it above
            writer = csv.writer(csvfile)

            for database in databases:
                print(f"Executing query on database: {database}")
                try:
                    # Switch to the current database
                    connection.database = database
                    cursor.execute(sql_query)
                    results = cursor.fetchall()

                    # Only write rows if results are found
                    if results:
                         # Write header once using description from the first successful query
                        if not header_written:
                            col_names = [desc[0] for desc in cursor.description]
                            writer.writerow(['Database', *col_names])
                            header_written = True
                            print("Wrote CSV header.")

                        # Write the data rows
                        for row in results:
                            writer.writerow([database, *row]) # Prepend database name
                        print(f"Wrote {len(results)} rows for database '{database}'.")
                    else:
                        print(f"No results found in database '{database}'.")

                except Error as e:
                    print(f"Error on database '{database}': {e}")
                except Exception as e:
                    print(f"An unexpected error occurred processing database '{database}': {e}")


    except Error as e:
        print(f"Error connecting to MariaDB or during database listing: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during database operations: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed.")

if __name__ == "__main__":
    # Read the SQL query from the file specified in .env (or default)
    sql_query = read_query_from_file(SQL_FILE)

    # --- Dynamic CSV filename construction ---
    # Get today's date in YYYY_MM_DD format
    today_formatted = datetime.now().strftime('%Y_%m_%d')

    # Get the DB_HOST value. This should be set in the remote .env file.
    # If DB_HOST is not set, use a default label or raise an error.
    db_host_label = DB_HOST if DB_HOST else "unknown_host"
    # Clean up hostname for filename (e.g., remove periods, slashes)
    db_host_label = db_host_label.replace('.', '_').replace('/', '_')

    # Construct the output CSV file name
    output_csv_filename = f"{db_host_label}_{today_formatted}.csv"
    # Construct the full output path within the OUTPUT_DIR
    output_csv_full_path = os.path.join(OUTPUT_DIR, output_csv_filename)
    # --- End dynamic CSV filename construction ---

    # Execute the query on all databases, writing results to the dynamically named CSV
    execute_query_on_all_databases(sql_query, output_csv_full_path)
    print(f"REPORT_PATH:{output_csv_full_path}")

    
