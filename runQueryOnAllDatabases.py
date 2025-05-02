import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import csv

# Load environment variables from the .env file
load_dotenv()

# Database connection parameters
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_PORT = int(os.getenv('DB_PORT', 3306))
SQL_FILE = os.getenv('SQL_FILE')

def read_query_from_file(file_path):
    """Read the SQL query from the specified file."""
    with open(file_path, 'r') as file:
        return file.read()

def execute_query_on_all_databases(sql_query, output_csv):
    try:
        # Connect to the MariaDB server
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            # Retrieve all databases
            cursor.execute("SHOW DATABASES;")
            databases = cursor.fetchall()

            # Open the CSV file for writing
            with open(output_csv, mode='w', newline='', encoding='utf-8') as csvfile:
                csv_writer = csv.writer(csvfile)

                for (database,) in databases:
                    print(f"Executing query on database: {database}")
                    try:
                        # Switch to the current database
                        connection.database = database
                        # Execute the SQL query
                        cursor.execute(sql_query)
                        results = cursor.fetchall()

                        # Write results to CSV
                        if results:
                            # Write the database name as a header
                            csv_writer.writerow([f"Results from database: {database}"])
                            # Write the column headers (if applicable)
                            column_headers = [i[0] for i in cursor.description]
                            csv_writer.writerow(column_headers)
                            # Write the data rows
                            csv_writer.writerows(results)
                            csv_writer.writerow([])  # Add a blank line for separation
                        else:
                            print(f"No results found in database {database}.")

                    except Error as e:
                        print(f"Error executing query on database {database}: {e}")

    except Error as e:
        print(f"Error connecting to MariaDB: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed.")

if __name__ == "__main__":
    # Read the SQL query from the file
    if SQL_FILE:
        sql_query = read_query_from_file(SQL_FILE)
        
        # Construct the output CSV file name based on the SQL file name
        base_name = os.path.splitext(SQL_FILE)[0]  # Get the base name without extension
        output_csv = f"{base_name}_output.csv"  # Create the output CSV file name
        
        execute_query_on_all_databases(sql_query, output_csv)
    else:
        print("SQL file not specified in the .env file.")
