
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


# Employee data validation
def validate_employee(row):
    if row.get("id") is None:
        raise ValueError("Employee ID cannot be empty")

    if not row.get("name") or not row["name"].strip():
        raise ValueError(f"Invalid employee name for ID {row.get('id')}")

    if not row.get("department") or not row["department"].strip():
        raise ValueError(
            f"Invalid department for employee ID {row.get('id')}"
        )

    logger.info("Employee validation passed for ID %s", row["id"])


# Product data validation
def validate_product(row):
    if row.get("id") is None:
        raise ValueError("Product ID cannot be empty")

    if not row.get("name") or not row["name"].strip():
        raise ValueError(f"Invalid product name for ID {row.get('id')}")

    if row.get("price") is None:
        raise ValueError(f"Product price is missing for ID {row.get('id')}")

    if float(row["price"]) < 0:
        raise ValueError(f"Negative price for product ID {row.get('id')}")

    logger.info("Product validation passed for ID %s", row["id"])


def migrate_data():
    connection = None
    cursor = None

    try:
        logger.info("Starting employee migration")

        connection = get_mysql_connection()
        redis_client = get_redis_connection()

        redis_client.ping()
        logger.info("Redis connection successful")

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
            # Validate before migrating
            validate_employee(row)

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

    except Exception:
        logger.exception("Employee migration failed")
        raise

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()
            logger.info("MySQL connection closed")


def migrate_products():
    connection = None
    cursor = None

    try:
        logger.info("Starting product migration")

        connection = get_mysql_connection()
        redis_client = get_redis_connection()

        redis_client.ping()
        logger.info("Redis connection successful")

        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT id, name, price FROM products ORDER BY id"
        )

        rows = cursor.fetchall()

        logger.info("Fetched %d product records", len(rows))

        for row in rows:
            # Validate before migrating
            validate_product(row)

            # Convert Decimal to JSON-compatible float
            row["price"] = float(row["price"])

            key = f"product:{row['id']}"
            redis_client.set(key, json.dumps(row))

            logger.info("Saved %s", key)

        logger.info(
            "Product migration completed successfully: %d records",
            len(rows)
        )

    except Exception:
        logger.exception("Product migration failed")
        raise

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()
            logger.info("MySQL connection closed")


if __name__ == "__main__":
    try:
        logger.info("SQL-to-Redis migration pipeline started")

        migrate_data()
        migrate_products()

        logger.info("SQL-to-Redis migration pipeline finished successfully")

    except Exception:
        logger.exception("SQL-to-Redis pipeline failed")
        raise
