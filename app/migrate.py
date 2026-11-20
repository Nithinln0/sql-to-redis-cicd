
import json
import os
import logging

import mysql.connector
import redis

CHECKPOINT_KEY = "migration:last_success"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def get_mysql_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3307")),
        user=os.getenv("MYSQL_USER", "appuser"),
        password=os.getenv("MYSQL_PASSWORD", "apppass123"),
        database=os.getenv("MYSQL_DATABASE", "company"),
    )


def get_redis_connection():
    return redis.Redis(
        host=os.getenv("REDIS_HOST", "127.0.0.1"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        decode_responses=True,
    )


def migrate_data():
    logger.info("Starting employee migration")

    connection = get_mysql_connection()
    redis_client = get_redis_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        checkpoint = redis_client.get(CHECKPOINT_KEY)

        if checkpoint:
            logger.info("Checkpoint found: %s", checkpoint)

            cursor.execute(
                """
                SELECT id, name, department, updated_at
                FROM employees
                WHERE updated_at > %s
                ORDER BY updated_at, id
                """,
                (checkpoint,),
            )
        else:
            logger.info("No checkpoint found. Running full employee migration")

            cursor.execute(
                """
                SELECT id, name, department, updated_at
                FROM employees
                ORDER BY updated_at, id
                """
            )

        rows = cursor.fetchall()

        logger.info("Fetched %d employee records", len(rows))

        for row in rows:
            updated_at = row.pop("updated_at")

            row["updated_at"] = (
                updated_at.isoformat(sep=" ")
                if updated_at
                else None
            )

            key = f"employee:{row['id']}"
            redis_client.set(key, json.dumps(row))

            logger.info("Saved %s", key)

        if rows:
            latest = max(row["updated_at"] for row in rows)
            redis_client.set(CHECKPOINT_KEY, latest)
            logger.info("Checkpoint updated: %s", latest)

        logger.info(
            "Employee migration completed successfully: %d records",
            len(rows)
        )

    finally:
        connection.close()


def migrate_products():
    logger.info("Starting product migration")

    connection = get_mysql_connection()
    redis_client = get_redis_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT id, name, price FROM products ORDER BY id"
        )

        rows = cursor.fetchall()

        logger.info("Fetched %d product records", len(rows))

        for row in rows:
            # Convert MySQL Decimal to JSON-compatible float
            row["price"] = float(row["price"])

            key = f"product:{row['id']}"
            redis_client.set(key, json.dumps(row))

            logger.info("Saved %s", key)

        logger.info(
            "Product migration completed successfully: %d records",
            len(rows)
        )

    finally:
        connection.close()


if __name__ == "__main__":
    logger.info("SQL-to-Redis migration pipeline started")

    migrate_data()
    migrate_products()

    logger.info("SQL-to-Redis migration pipeline finished")
