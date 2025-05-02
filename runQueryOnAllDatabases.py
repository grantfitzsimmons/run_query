import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import csv

# Load environment variables from the .env file
load_dotenv()

# Database connection parameters
DB_HOST     = os.getenv('DB_HOST')
DB_USER     = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_PORT     = int(os.getenv('DB_PORT', 3306))
SQL_FILE    = os.getenv('SQL_FILE')

def read_query_from_file(file_path):
    """Read the SQL query from the specified file."""
    with open(file_path, 'r') as f:
        return f.read()

def execute_query_on_all_databases(sql_query, output_csv):
    connection = None
    try:
        # Connect to the MariaDB server
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
        cursor.execute("SHOW DATABASES;")
        databases = [row[0] for row in cursor.fetchall()]

        # Check if CSV exists (to avoid rewriting headers)
        file_exists    = os.path.exists(output_csv)
        header_written = file_exists

        # Open CSV in append mode
        with open(output_csv, mode='a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            for database in databases:
                print(f"Executing query on database: {database}")
                try:
                    # Switch to the current database
                    connection.database = database
                    cursor.execute(sql_query)
                    results = cursor.fetchall()

                    if not results:
                        print(f"No results found in database '{database}'.")
                        continue

                    # Write header if not already done
                    if not header_written:
                        col_names = [desc[0] for desc in cursor.description]
                        writer.writerow(['Database', *col_names])
                        header_written = True

                    # Write each row, prefixing with the database name
                    for row in results:
                        writer.writerow([database, *row])

                except Error as e:
                    print(f"Error executing query on database '{database}': {e}")

    except Error as e:
        print(f"Error connecting to MariaDB: {e}")

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection closed.")

if __name__ == "__main__":
    if not SQL_FILE:
        print("SQL_FILE not specified in environment.")
    else:
        sql_query = read_query_from_file(SQL_FILE)
        base_name  = os.path.splitext(SQL_FILE)[0]
        output_csv = f"{base_name}_output.csv"
        execute_query_on_all_databases(sql_query, output_csv)
