QUERIES = {

    # 1️⃣ Find flights between two airports
    "find_flights": """
        MATCH (from:Airport {station_code: $from_airport})
              <-[:DEPARTS_FROM]-(f:Flight)-[:ARRIVES_AT]->
              (to:Airport {station_code: $to_airport})
        OPTIONAL MATCH (j:Journey)-[:ON]->(f)
        RETURN from, f, j, to
    """,

    # 2️⃣ Delay analysis (based on Journey.delay)
    "delay_analysis": """
        MATCH (f:Flight)-[:ARRIVES_AT]->(a:Airport)
        OPTIONAL MATCH (j:Journey)-[:ON]->(f)
        RETURN f, j, a
        ORDER BY j.arrival_delay_minutes DESC
        LIMIT 20
    """,

    # 3️⃣ Airport info (full node)
    "airport_info": """
        MATCH (a:Airport {station_code: $station_code})
        OPTIONAL MATCH (f:Flight)-[:DEPARTS_FROM]->(a)
        OPTIONAL MATCH (f2:Flight)-[:ARRIVES_AT]->(a)
        RETURN a, f, f2
    """,

    # 4️⃣ Passenger experience (feedback, satisfaction, class, etc.)
    "passenger_experience": """
        MATCH (p:Passenger)-[:TOOK]->(j:Journey)-[:ON]->(f:Flight)
        RETURN p, j, f
        ORDER BY j.food_satisfaction_score ASC
        LIMIT 30
    """,

    # 5️⃣ Route recommendation (based on delays + miles + legs)
    "route_recommendation": """
        MATCH (f:Flight)-[:DEPARTS_FROM]->(from:Airport)
        MATCH (f)-[:ARRIVES_AT]->(to:Airport)
        OPTIONAL MATCH (j:Journey)-[:ON]->(f)
        RETURN from, f, j, to
        ORDER BY j.arrival_delay_minutes ASC, j.actual_flown_miles ASC
        LIMIT 20
    """,

    # 6️⃣ Fallback general query → return sample graph
    "general_query": """
        MATCH (n)
        RETURN n
        LIMIT 25
    """,

    # 7️⃣ Most delayed flights
    "most_delayed_flights": """
        MATCH (f:Flight)-[:ON]->(j:Journey)
        RETURN f, j
        ORDER BY j.arrival_delay_minutes DESC
        LIMIT 20
    """,

    # 8️⃣ Shortest journeys
    "shortest_journeys": """
        MATCH (j:Journey)-[:ON]->(f:Flight)
        RETURN j, f
        ORDER BY j.actual_flown_miles ASC
        LIMIT 20
    """,

    # 9️⃣ Multi-leg journeys
    "multi_leg_flights": """
        MATCH (j:Journey)-[:ON]->(f:Flight)
        WHERE j.number_of_legs > 1
        RETURN j, f
        LIMIT 20
    """,

    # 🔟 Loyalty-based passenger analysis
    "loyalty_analysis": """
        MATCH (p:Passenger)-[:TOOK]->(j:Journey)-[:ON]->(f:Flight)
        RETURN p, j, f
        ORDER BY p.loyalty_program_level DESC
        LIMIT 20
    """
}
