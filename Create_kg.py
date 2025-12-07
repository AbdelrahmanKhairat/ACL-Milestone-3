from neo4j import GraphDatabase
import csv

def load_config(path="config.txt"):
    config = {}
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or "=" not in line:
                continue
            key, value = line.split("=", 1)
            config[key.strip()] = value.strip()
    return config

def create_constraints(session):
    session.run("""
        CREATE CONSTRAINT passenger_record_locator_unique IF NOT EXISTS
        FOR (p:Passenger)
        REQUIRE p.record_locator IS UNIQUE
    """)

    session.run("""
        CREATE CONSTRAINT journey_feedback_id_unique IF NOT EXISTS
        FOR (j:Journey)
        REQUIRE j.feedback_ID IS UNIQUE
    """)

    session.run("""
        CREATE CONSTRAINT airport_code_unique IF NOT EXISTS
        FOR (a:Airport)
        REQUIRE a.station_code IS UNIQUE
    """)

    session.run("""
        CREATE CONSTRAINT flight_number_unique IF NOT EXISTS
        FOR (f:Flight)
        REQUIRE (f.flight_number, f.fleet_type_description) IS UNIQUE
    """)

def insert_row(session, row):
    # 1) Convert numeric fields properly
    arrival_delay_minutes = int(row["arrival_delay_minutes"])
    number_of_legs = int(row["number_of_legs"])
    actual_flown_miles = int(row["actual_flown_miles"])
    food_satisfaction_score = int(row["food_satisfaction_score"])

    params = {
        "record_locator": row["record_locator"],
        "loyalty_program_level": row["loyalty_program_level"],
        "generation": row["generation"],

        "feedback_ID": row["feedback_ID"],
        "food_satisfaction_score": food_satisfaction_score,
        "arrival_delay_minutes": arrival_delay_minutes,
        "actual_flown_miles": actual_flown_miles,
        "number_of_legs": number_of_legs,
        "passenger_class": row["passenger_class"],

        "flight_number": row["flight_number"],
        "fleet_type_description": row["fleet_type_description"],

        "origin_station": row["origin_station_code"],
        "destination_station": row["destination_station_code"],
    }

    cypher = """
    MERGE (p:Passenger {record_locator: $record_locator})
    SET  p.loyalty_program_level = $loyalty_program_level,
         p.generation = $generation

    MERGE (j:Journey {feedback_ID: $feedback_ID})
    SET  j.food_satisfaction_score = $food_satisfaction_score,
         j.arrival_delay_minutes   = $arrival_delay_minutes,
         j.actual_flown_miles      = $actual_flown_miles,
         j.number_of_legs          = $number_of_legs,
         j.passenger_class         = $passenger_class

    MERGE (f:Flight {flight_number: $flight_number, fleet_type_description: $fleet_type_description})

    MERGE (o:Airport {station_code: $origin_station})
    MERGE (d:Airport {station_code: $destination_station})

    MERGE (p)-[:TOOK]->(j)
    MERGE (j)-[:ON]->(f)
    MERGE (f)-[:DEPARTS_FROM]->(o)
    MERGE (f)-[:ARRIVES_AT]->(d)
    """

    session.run(cypher, params)

def load_rule(path="rule.txt"):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
    
def run_rule(session):
    rule_query = load_rule()
    result = session.run(rule_query)
    record = result.single()
    print("Rule result:", record)

def main():
    cfg = load_config()
    uri = cfg["URI"]
    user = cfg["USERNAME"]
    password = cfg["PASSWORD"]

    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        create_constraints(session)
        print("Constraints created.")

        # 🧨 VERY IMPORTANT: wipe existing data, but NOT constraints
        session.run("MATCH (n) DETACH DELETE n")
        print("Existing data deleted.")

        with open("Airline_surveys_sample.csv", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                insert_row(session, row)
                count += 1
                if count % 100 == 0:
                    print(f"Inserted {count} rows...")

        print(f"Done. Inserted {count} rows.")

        run_rule(session)

    driver.close()

if __name__ == "__main__":
    main()
