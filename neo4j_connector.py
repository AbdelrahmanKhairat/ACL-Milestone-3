# neo4j_connector.py
from neo4j import GraphDatabase

def load_config(path="config.txt"):
    config = {}
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, value = line.split("=", 1)
            config[key.strip()] = value.strip()
    return config

config = load_config()

URI = config["URI"]          # neo4j://127.0.0.1:7687
USERNAME = config["USERNAME"]
PASSWORD = config["PASSWORD"]

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

def run_query(query, params=None):
    if params is None:
        params = {}
    with driver.session() as session:
        result = session.run(query, params)
        # Return list of dicts
        return [record.data() for record in result]
