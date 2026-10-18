import os
import pandas as pd
from sqlalchemy import URL, create_engine, text
from dotenv import load_dotenv
from pathlib import Path

def ingest_data():
    # Load environment variables from .env file
    load_dotenv()

    #1. dynnamically resolve project root based on the location of this script
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    #2. build absolute path to the data file
    data_file_path = project_root / 'data' / 'MIMIC_IV_Transcript.csv'
    schema_file_path = project_root / 'src' / 'database' / 'schema.sql'

    #3. verify that the data file exists
    if not data_file_path.exists():
        raise FileNotFoundError(f"Data file not found at {data_file_path}")
    
    # URL.create escapes special characters in the password (e.g. @, :, /)
    db_name = os.getenv('DB_NAME', 'ehr_db')
    db_url = URL.create(
        "postgresql+psycopg2",
        username=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        database=db_name,
    )

    #4. create the target database if it does not exist yet
    # (connect to the default 'postgres' database; CREATE DATABASE needs autocommit)
    admin_engine = create_engine(db_url.set(database='postgres'), isolation_level='AUTOCOMMIT')
    with admin_engine.connect() as connection:
        exists = connection.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": db_name}
        ).scalar()
        if not exists:
            print(f"creating database: {db_name}")
            connection.execute(text(f'CREATE DATABASE "{db_name}"'))
    admin_engine.dispose()

    engine = create_engine(db_url)

    #5. run the schema file, skipping it if it is empty
    schema_sql = schema_file_path.read_text().strip()
    if schema_sql:
        print(f"executing schema file: {schema_file_path}")
        with engine.begin() as connection:
            connection.execute(text(schema_sql))
    else:
        print(f"schema file is empty, skipping: {schema_file_path}")

    print(f"ingesting data from: {data_file_path}")
    # low_memory=False reads the whole file before inferring types (avoids mixed-type warning)
    df = pd.read_csv(data_file_path, low_memory=False)

    #replace NAN/NAT with None
    df = df.where(pd.notnull(df), None)

    print(f"ingesting {len(df)} records into remote AWS postgresSQL instance")
    df.to_sql('patient_encounters', con=engine, if_exists='replace', index=False,
              method='multi', chunksize=1000)

    print("Data ingestion completed successfully.")

if __name__ == "__main__":
    ingest_data()