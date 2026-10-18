import os
import pandas as pd
from sqlalchemy import URL, create_engine, text
from dotenv import load_dotenv

def verify_ingestion():
    # Load environment variables from .env file
    load_dotenv()

    db_name = os.getenv('DB_NAME', 'ehr_db')
    db_url = URL.create(
        "postgresql+psycopg2",
        username=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        database=db_name,
    )
    engine = create_engine(db_url)

    print(f"verifying data integrity in the database: {db_name}")

    with engine.connect() as connection:
        #1 check total row count
        row_count = connection.execute(text("SELECT COUNT(*) FROM patient_encounters")).scalar()
        print(f"total row count in patient_encounters: {row_count}")

        if row_count == 0:
            print("Warning: No data found in patient_encounters table. Please check the ingestion process.")
            return

        #2 retrive sample of critical clinical columns
        # we select specific columns so the terminal output is readable
        print("\nfetching sample of critical clinical columns from patient_encounters:")
        query = text("""
                     SELECT
                         subject_id,
                         admission_type,
                         drug,
                         drg_severity
                     FROM patient_encounters
                     LIMIT 5
         """)

        # use pandas for clean terminal formatting
        sample_data = pd.read_sql(query, connection)

        print("-"*50)
        print(sample_data.to_string(index=False))
        print("-"*50)

if __name__ == "__main__":
    verify_ingestion()
