
import json
import os
import time

import mysql.connector
import redis


def migrate_data():
    # Connect to MySQL
    connection = mysql.connector.connect(
        host="127.0.0.1",
        port=3307,
        user="appuser",
        password="apppass123",
        database="company",
    )

    # Connect to Redis
    redis_client = redis.Redis(
        host="127.0.0.1",
        port=6379,
        decode_responses=True,
    )

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, name, department FROM employees"
        )
        rows = cursor.fetchall()

        for row in rows:
            key = f"employee:{row['id']}"
            value = json.dumps(row)
            redis_client.set(key, value)
            print(f"Saved {key} -> {value}")

        print(f"Migration completed: {len(rows)} records")

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    migrate_data()
