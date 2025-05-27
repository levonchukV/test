import time
import psycopg2
import os

def wait_for_db():
    max_tries = 30
    while max_tries > 0:
        try:
            conn = psycopg2.connect(
                dbname=os.getenv("POSTGRES_DB", "tododb"),
                user=os.getenv("POSTGRES_USER", "postgres"),
                password=os.getenv("POSTGRES_PASSWORD", "postgres"),
                host=os.getenv("POSTGRES_HOST", "db"),
                port=os.getenv("POSTGRES_PORT", "5432")
            )
            conn.close()
            print("Database is ready!")
            return True
        except psycopg2.OperationalError:
            print("Waiting for database...")
            max_tries -= 1
            time.sleep(1)
    
    print("Could not connect to database")
    return False 