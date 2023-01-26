import argparse
from sqlalchemy import create_engine, types
import pandas as pd
import time


# Create a dictionary to map pandas data types to PostgreSQL data types
pandas_to_sqlalchemy = {
    'int64': types.Integer,
    'float64': types.Float,
    'object': types.String,
    'bool': types.Boolean,
    'datetime64[ns]': types.DateTime,
}

start_time = time.time()

# Create the parser
parser = argparse.ArgumentParser(description="A script to create table from csv")

# Add the arguments
parser.add_argument("--host", help="hostname of the postgresql")
parser.add_argument("--port", type=int, help="port number of the postgresql")
parser.add_argument("--database", help="database name")
parser.add_argument("--user", help="username")
parser.add_argument("--password", help="password")
parser.add_argument("--url", help="url of the csv file")
parser.add_argument("--table_name", help="name of the table to be created")
parser.add_argument(
    "--date_columns", nargs="+", required=False, help="date columns", default=None
)
parser.add_argument(
    "--chunk_size", type=int, required=False, help="chunk size", default=1000
)

# Parse the arguments
args = parser.parse_args()

# Get the connection details, CSV URL, and table name from the arguments
host = args.host
port = args.port
database = args.database
user = args.user
password = args.password
url = args.url
table_name = args.table_name
date_columns = args.date_columns
chunk_size = args.chunk_size
# If date columns are not provided, parse_dates will be None
parse_dates = date_columns if date_columns else None

try:
    engine = create_engine(f"postgresql://{user}:{password}@{host}:{port}/{database}")

    # Read the first row of the CSV file
    df = pd.read_csv(url, nrows=1)

    # Get the datatype of each column
    dtype = {col: pandas_to_sqlalchemy[df[col].dtype.name] for col in df.columns}

    for col in date_columns:
        dtype[col] = types.DateTime

    # Create the table
    df.to_sql(table_name, engine, if_exists='replace', index=False, dtype=dtype)

    # Get the total number of rows in the CSV file
    total_rows = sum(1 for line in open(url)) - 1

    # Read the CSV file in chunks
    for i, chunk in enumerate(
        pd.read_csv(url, parse_dates=parse_dates, chunksize=chunk_size)
    ):

        # Insert the data into the table
        chunk.to_sql(table_name, engine, if_exists="append", index=False)
        print(f"Processed {(i+1)*chunk_size}/{total_rows} rows.")

    end_time = time.time()
    time_elapsed = end_time - start_time

    print(f"Time elapsed: {time_elapsed:.2f} seconds")
    print(f"Total rows: {total_rows}")

except Exception as e:
    print(e)
