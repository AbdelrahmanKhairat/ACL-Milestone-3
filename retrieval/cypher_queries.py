# retrieval/cypher_queries.py
"""
Enhanced Cypher Query Templates
================================
All queries now return complete Journey context with:
- Journey properties (delay, miles, legs, food score, class)
- Flight information (number, fleet type)
- Airport codes (departure/arrival)
- Passenger information (generation, loyalty level, record locator)

This matches the structure of embedding search results for easier combination.

ALL queries support optional filtering based on extracted entities.
"""

QUERIES = {

    # 1️⃣ Find flights between two airports - ENHANCED with optional filters
    "find_flights": """
        MATCH (p:Passenger)-[:TOOK]->(j:Journey)-[:ON]->(f:Flight)
        MATCH (f)-[:DEPARTS_FROM]->(dep:Airport)
        MATCH (f)-[:ARRIVES_AT]->(arr:Airport)
        WHERE ($from_airport IS NULL OR dep.station_code = $from_airport)
          AND ($to_airport IS NULL OR arr.station_code = $to_airport)
          AND ($passenger_class IS NULL OR j.passenger_class = $passenger_class)
          AND ($generation IS NULL OR p.generation = $generation)
          AND ($number_of_legs IS NULL OR j.number_of_legs = $number_of_legs)
        RETURN j.feedback_ID as feedback_ID,
               j.passenger_class as passenger_class,
               j.food_satisfaction_score as food_satisfaction_score,
               j.arrival_delay_minutes as arrival_delay_minutes,
               j.actual_flown_miles as actual_flown_miles,
               j.number_of_legs as number_of_legs,
               f.flight_number as flight_number,
               f.fleet_type_description as fleet_type,
               dep.station_code as departure_airport,
               arr.station_code as arrival_airport,
               p.generation as generation,
               p.loyalty_program_level as loyalty_level,
               p.record_locator as record_locator
        LIMIT $limit
    """,

    # 2️⃣ General delay analysis - ENHANCED with optional filters
    "delay_analysis": """
        MATCH (p:Passenger)-[:TOOK]->(j:Journey)-[:ON]->(f:Flight)
        MATCH (f)-[:DEPARTS_FROM]->(dep:Airport)
        MATCH (f)-[:ARRIVES_AT]->(arr:Airport)
        WHERE ($from_airport IS NULL OR dep.station_code = $from_airport)
          AND ($to_airport IS NULL OR arr.station_code = $to_airport)
          AND ($passenger_class IS NULL OR j.passenger_class = $passenger_class)
          AND ($generation IS NULL OR p.generation = $generation)
          AND ($number_of_legs IS NULL OR j.number_of_legs = $number_of_legs)
        RETURN j.feedback_ID as feedback_ID,
               j.passenger_class as passenger_class,
               j.food_satisfaction_score as food_satisfaction_score,
               j.arrival_delay_minutes as arrival_delay_minutes,
               j.actual_flown_miles as actual_flown_miles,
               j.number_of_legs as number_of_legs,
               f.flight_number as flight_number,
               f.fleet_type_description as fleet_type,
               dep.station_code as departure_airport,
               arr.station_code as arrival_airport,
               p.generation as generation,
               p.loyalty_program_level as loyalty_level,
               p.record_locator as record_locator
        ORDER BY j.arrival_delay_minutes DESC
        LIMIT $limit
    """,

    # 3️⃣ Airport info - ENHANCED with optional filters
    "airport_info": """
        MATCH (p:Passenger)-[:TOOK]->(j:Journey)-[:ON]->(f:Flight)
        MATCH (f)-[:DEPARTS_FROM]->(dep:Airport)
        MATCH (f)-[:ARRIVES_AT]->(arr:Airport)
        WHERE ($station_code IS NULL OR dep.station_code = $station_code OR arr.station_code = $station_code)
          AND ($passenger_class IS NULL OR j.passenger_class = $passenger_class)
          AND ($generation IS NULL OR p.generation = $generation)
          AND ($number_of_legs IS NULL OR j.number_of_legs = $number_of_legs)
        RETURN j.feedback_ID as feedback_ID,
               j.passenger_class as passenger_class,
               j.food_satisfaction_score as food_satisfaction_score,
               j.arrival_delay_minutes as arrival_delay_minutes,
               j.actual_flown_miles as actual_flown_miles,
               j.number_of_legs as number_of_legs,
               f.flight_number as flight_number,
               f.fleet_type_description as fleet_type,
               dep.station_code as departure_airport,
               arr.station_code as arrival_airport,
               p.generation as generation,
               p.loyalty_program_level as loyalty_level,
               p.record_locator as record_locator
        LIMIT $limit
    """,

    # 4️⃣ Passenger experience - ENHANCED with optional filters
    "passenger_experience": """
        MATCH (p:Passenger)-[:TOOK]->(j:Journey)-[:ON]->(f:Flight)
        MATCH (f)-[:DEPARTS_FROM]->(dep:Airport)
        MATCH (f)-[:ARRIVES_AT]->(arr:Airport)
        WHERE ($from_airport IS NULL OR dep.station_code = $from_airport)
          AND ($to_airport IS NULL OR arr.station_code = $to_airport)
          AND ($passenger_class IS NULL OR j.passenger_class = $passenger_class)
          AND ($generation IS NULL OR p.generation = $generation)
          AND ($number_of_legs IS NULL OR j.number_of_legs = $number_of_legs)
        RETURN j.feedback_ID as feedback_ID,
               j.passenger_class as passenger_class,
               j.food_satisfaction_score as food_satisfaction_score,
               j.arrival_delay_minutes as arrival_delay_minutes,
               j.actual_flown_miles as actual_flown_miles,
               j.number_of_legs as number_of_legs,
               f.flight_number as flight_number,
               f.fleet_type_description as fleet_type,
               dep.station_code as departure_airport,
               arr.station_code as arrival_airport,
               p.generation as generation,
               p.loyalty_program_level as loyalty_level,
               p.record_locator as record_locator
        ORDER BY j.food_satisfaction_score ASC
        LIMIT $limit
    """,

    # 5️⃣ Route recommendation - ENHANCED with optional filters
    "route_recommendation": """
        MATCH (p:Passenger)-[:TOOK]->(j:Journey)-[:ON]->(f:Flight)
        MATCH (f)-[:DEPARTS_FROM]->(dep:Airport)
        MATCH (f)-[:ARRIVES_AT]->(arr:Airport)
        WHERE ($from_airport IS NULL OR dep.station_code = $from_airport)
          AND ($to_airport IS NULL OR arr.station_code = $to_airport)
          AND ($passenger_class IS NULL OR j.passenger_class = $passenger_class)
          AND ($generation IS NULL OR p.generation = $generation)
          AND ($number_of_legs IS NULL OR j.number_of_legs = $number_of_legs)
        RETURN j.feedback_ID as feedback_ID,
               j.passenger_class as passenger_class,
               j.food_satisfaction_score as food_satisfaction_score,
               j.arrival_delay_minutes as arrival_delay_minutes,
               j.actual_flown_miles as actual_flown_miles,
               j.number_of_legs as number_of_legs,
               f.flight_number as flight_number,
               f.fleet_type_description as fleet_type,
               dep.station_code as departure_airport,
               arr.station_code as arrival_airport,
               p.generation as generation,
               p.loyalty_program_level as loyalty_level,
               p.record_locator as record_locator
        ORDER BY j.arrival_delay_minutes ASC, j.actual_flown_miles ASC, j.food_satisfaction_score DESC
        LIMIT $limit
    """,

    # 6️⃣ General query - ENHANCED with optional filters
    "general_query": """
        MATCH (p:Passenger)-[:TOOK]->(j:Journey)-[:ON]->(f:Flight)
        MATCH (f)-[:DEPARTS_FROM]->(dep:Airport)
        MATCH (f)-[:ARRIVES_AT]->(arr:Airport)
        WHERE ($from_airport IS NULL OR dep.station_code = $from_airport)
          AND ($to_airport IS NULL OR arr.station_code = $to_airport)
          AND ($passenger_class IS NULL OR j.passenger_class = $passenger_class)
          AND ($generation IS NULL OR p.generation = $generation)
          AND ($number_of_legs IS NULL OR j.number_of_legs = $number_of_legs)
        RETURN j.feedback_ID as feedback_ID,
               j.passenger_class as passenger_class,
               j.food_satisfaction_score as food_satisfaction_score,
               j.arrival_delay_minutes as arrival_delay_minutes,
               j.actual_flown_miles as actual_flown_miles,
               j.number_of_legs as number_of_legs,
               f.flight_number as flight_number,
               f.fleet_type_description as fleet_type,
               dep.station_code as departure_airport,
               arr.station_code as arrival_airport,
               p.generation as generation,
               p.loyalty_program_level as loyalty_level,
               p.record_locator as record_locator
        LIMIT $limit
    """,

    # 7️⃣ Most delayed flights - ENHANCED with optional filters
    "most_delayed_flights": """
        MATCH (p:Passenger)-[:TOOK]->(j:Journey)-[:ON]->(f:Flight)
        MATCH (f)-[:DEPARTS_FROM]->(dep:Airport)
        MATCH (f)-[:ARRIVES_AT]->(arr:Airport)
        WHERE j.arrival_delay_minutes > 0
          AND ($from_airport IS NULL OR dep.station_code = $from_airport)
          AND ($to_airport IS NULL OR arr.station_code = $to_airport)
          AND ($passenger_class IS NULL OR j.passenger_class = $passenger_class)
          AND ($generation IS NULL OR p.generation = $generation)
          AND ($number_of_legs IS NULL OR j.number_of_legs = $number_of_legs)
        RETURN j.feedback_ID as feedback_ID,
               j.passenger_class as passenger_class,
               j.food_satisfaction_score as food_satisfaction_score,
               j.arrival_delay_minutes as arrival_delay_minutes,
               j.actual_flown_miles as actual_flown_miles,
               j.number_of_legs as number_of_legs,
               f.flight_number as flight_number,
               f.fleet_type_description as fleet_type,
               dep.station_code as departure_airport,
               arr.station_code as arrival_airport,
               p.generation as generation,
               p.loyalty_program_level as loyalty_level,
               p.record_locator as record_locator
        ORDER BY j.arrival_delay_minutes DESC
        LIMIT $limit
    """,

    # 8️⃣ Shortest journeys - ENHANCED with optional filters
    "shortest_journeys": """
        MATCH (p:Passenger)-[:TOOK]->(j:Journey)-[:ON]->(f:Flight)
        MATCH (f)-[:DEPARTS_FROM]->(dep:Airport)
        MATCH (f)-[:ARRIVES_AT]->(arr:Airport)
        WHERE ($from_airport IS NULL OR dep.station_code = $from_airport)
          AND ($to_airport IS NULL OR arr.station_code = $to_airport)
          AND ($passenger_class IS NULL OR j.passenger_class = $passenger_class)
          AND ($generation IS NULL OR p.generation = $generation)
          AND ($number_of_legs IS NULL OR j.number_of_legs = $number_of_legs)
        RETURN j.feedback_ID as feedback_ID,
               j.passenger_class as passenger_class,
               j.food_satisfaction_score as food_satisfaction_score,
               j.arrival_delay_minutes as arrival_delay_minutes,
               j.actual_flown_miles as actual_flown_miles,
               j.number_of_legs as number_of_legs,
               f.flight_number as flight_number,
               f.fleet_type_description as fleet_type,
               dep.station_code as departure_airport,
               arr.station_code as arrival_airport,
               p.generation as generation,
               p.loyalty_program_level as loyalty_level,
               p.record_locator as record_locator
        ORDER BY j.actual_flown_miles ASC
        LIMIT $limit
    """,

    # 11 Longest journeys - ENHANCED with optional filters
    "longest_journeys": """
        MATCH (p:Passenger)-[:TOOK]->(j:Journey)-[:ON]->(f:Flight)
        MATCH (f)-[:DEPARTS_FROM]->(dep:Airport)
        MATCH (f)-[:ARRIVES_AT]->(arr:Airport)
        WHERE ($from_airport IS NULL OR dep.station_code = $from_airport)
          AND ($to_airport IS NULL OR arr.station_code = $to_airport)
          AND ($passenger_class IS NULL OR j.passenger_class = $passenger_class)
          AND ($generation IS NULL OR p.generation = $generation)
          AND ($number_of_legs IS NULL OR j.number_of_legs = $number_of_legs)
        RETURN j.feedback_ID as feedback_ID,
               j.passenger_class as passenger_class,
               j.food_satisfaction_score as food_satisfaction_score,
               j.arrival_delay_minutes as arrival_delay_minutes,
               j.actual_flown_miles as actual_flown_miles,
               j.number_of_legs as number_of_legs,
               f.flight_number as flight_number,
               f.fleet_type_description as fleet_type,
               dep.station_code as departure_airport,
               arr.station_code as arrival_airport,
               p.generation as generation,
               p.loyalty_program_level as loyalty_level,
               p.record_locator as record_locator
        ORDER BY j.actual_flown_miles DESC
        LIMIT $limit
    """,

    # 9️⃣ Multi-leg journeys - ENHANCED with optional filters
    "multi_leg_flights": """
        MATCH (p:Passenger)-[:TOOK]->(j:Journey)-[:ON]->(f:Flight)
        MATCH (f)-[:DEPARTS_FROM]->(dep:Airport)
        MATCH (f)-[:ARRIVES_AT]->(arr:Airport)
        WHERE j.number_of_legs > 1
          AND ($from_airport IS NULL OR dep.station_code = $from_airport)
          AND ($to_airport IS NULL OR arr.station_code = $to_airport)
          AND ($passenger_class IS NULL OR j.passenger_class = $passenger_class)
          AND ($generation IS NULL OR p.generation = $generation)
          AND ($number_of_legs IS NULL OR j.number_of_legs = $number_of_legs)
        RETURN j.feedback_ID as feedback_ID,
               j.passenger_class as passenger_class,
               j.food_satisfaction_score as food_satisfaction_score,
               j.arrival_delay_minutes as arrival_delay_minutes,
               j.actual_flown_miles as actual_flown_miles,
               j.number_of_legs as number_of_legs,
               f.flight_number as flight_number,
               f.fleet_type_description as fleet_type,
               dep.station_code as departure_airport,
               arr.station_code as arrival_airport,
               p.generation as generation,
               p.loyalty_program_level as loyalty_level,
               p.record_locator as record_locator
        ORDER BY j.number_of_legs DESC
        LIMIT $limit
    """,

    # 🔟 Loyalty-based passenger analysis - ENHANCED with optional filters
    "loyalty_analysis": """
        MATCH (p:Passenger)-[:TOOK]->(j:Journey)-[:ON]->(f:Flight)
        MATCH (f)-[:DEPARTS_FROM]->(dep:Airport)
        MATCH (f)-[:ARRIVES_AT]->(arr:Airport)
        WHERE ($from_airport IS NULL OR dep.station_code = $from_airport)
          AND ($to_airport IS NULL OR arr.station_code = $to_airport)
          AND ($passenger_class IS NULL OR j.passenger_class = $passenger_class)
          AND ($generation IS NULL OR p.generation = $generation)
          AND ($number_of_legs IS NULL OR j.number_of_legs = $number_of_legs)
        RETURN j.feedback_ID as feedback_ID,
               j.passenger_class as passenger_class,
               j.food_satisfaction_score as food_satisfaction_score,
               j.arrival_delay_minutes as arrival_delay_minutes,
               j.actual_flown_miles as actual_flown_miles,
               j.number_of_legs as number_of_legs,
               f.flight_number as flight_number,
               f.fleet_type_description as fleet_type,
               dep.station_code as departure_airport,
               arr.station_code as arrival_airport,
               p.generation as generation,
               p.loyalty_program_level as loyalty_level,
               p.record_locator as record_locator
        ORDER BY p.loyalty_program_level DESC
        LIMIT $limit
    """,

    # 🔟 Statistics Aggregation - NEW
    "calculate_statistic": """
        MATCH (p:Passenger)-[:TOOK]->(j:Journey)-[:ON]->(f:Flight)
        MATCH (f)-[:DEPARTS_FROM]->(dep:Airport)
        MATCH (f)-[:ARRIVES_AT]->(arr:Airport)
        WHERE ($from_airport IS NULL OR dep.station_code = $from_airport)
          AND ($to_airport IS NULL OR arr.station_code = $to_airport)
          AND ($passenger_class IS NULL OR j.passenger_class = $passenger_class)
          AND ($generation IS NULL OR p.generation = $generation)
          AND ($number_of_legs IS NULL OR j.number_of_legs = $number_of_legs)
        RETURN count(j) as total_journeys,
               avg(j.arrival_delay_minutes) as avg_delay,
               avg(j.food_satisfaction_score) as avg_food_score,
               avg(j.actual_flown_miles) as avg_distance,
               min(j.arrival_delay_minutes) as min_delay,
               max(j.arrival_delay_minutes) as max_delay
    """
}
