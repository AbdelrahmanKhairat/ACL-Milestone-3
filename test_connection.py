# test_connection.py
from neo4j_connector import run_query

if __name__ == "__main__":
    results = run_query("MATCH (n) RETURN n LIMIT 5")
    for row in results:
        print(row)
