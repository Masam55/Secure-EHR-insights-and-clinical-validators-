import os
from sqlalchemy import URL, create_engine, text
from dotenv import load_dotenv  


def apply_pgvector_schema():
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

    print(f"applying pgvector schema to the database: {db_name}")
    
    try:
        with engine.begin() as connection:
            # Note: pgvector extension must be installed in the database before running this script
            # we only alter the application table here.
            print("Adding clinical_embedding column(768-dimensional vector) to patient_encounters table..." )
            connection.execute(text("ALTER TABLE patient_encounters ADD COLUMN if not exists clinical_embedding vector(768)"))

            #  verify that the column was added successfully (must stay inside the with block,
            #  the connection is closed once the block exits)
            result = connection.execute(text("""
                        SELECT column_name, udt_name
                        FROM information_schema.columns
                        WHERE table_name='patient_encounters'
                        AND column_name='clinical_embedding';
                        """)).fetchone()

            if result:
                print(f"Successfully added column: {result[0]} with data type: {result[1]}")

            else:
                print("Failed to add clinical_embedding column to patient_encounters table.")
    
    except Exception as e:
        print(f"An error occurred while applying the pgvector schema: {e}") 
    
if __name__ == "__main__":
    apply_pgvector_schema()
        