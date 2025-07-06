import csv
import uuid
import mysql.connector
from mysql.connector import errorcode

DB_NAME = "ALX_prodev"
TABLE_NAME = "user_data"
CSV_FILE = "user_data.csv"

MYSQL_CONFIG = {
    'user': 'root',
    'password': 'user_pswd',
    'host': 'localhost',
}


def connect_db():
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        print("Connected to MySQL server.")
        return conn
    except mysql.connector.Error as err:
        print(f"Connection failed: {err}")
        exit(1)


def create_database(connection):
    cursor = connection.cursor()
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        print(f"Database `{DB_NAME}` ready.")
    finally:
        cursor.close()


def connect_to_prodev():
    try:
        config_with_db = MYSQL_CONFIG.copy()
        config_with_db["database"] = DB_NAME
        conn = mysql.connector.connect(**config_with_db)
        return conn
    except mysql.connector.Error as err:
        print(f"Failed to connect to `{DB_NAME}`: {err}")
        exit(1)


def create_table(connection):
    table_def = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        user_id CHAR(36) PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL,
        age DECIMAL(5,2) NOT NULL,
        INDEX(email)
    )
    """
    cursor = connection.cursor()
    try:
        cursor.execute(table_def)
        print(f"Table `{TABLE_NAME}` ready.")
    finally:
        cursor.close()


def insert_data(connection, data):
    cursor = connection.cursor()
    insert_query = f"""
    INSERT INTO {TABLE_NAME} (user_id, name, email, age)
    SELECT * FROM (SELECT %s, %s, %s, %s) AS tmp
    WHERE NOT EXISTS (
        SELECT 1 FROM {TABLE_NAME} WHERE email = %s
    )
    """
    try:
        for row in data:
            user_id = str(uuid.uuid4())
            name, email, age = row
            cursor.execute(insert_query, (user_id, name, email, age, email))
        connection.commit()
        print("Data inserted successfully.")
    finally:
        cursor.close()


def read_csv_data(filename):
    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip header if present
        return [tuple(row) for row in reader]


if __name__ == "__main__":
    conn = connect_db()
    create_database(conn)
    conn.close()

    db_conn = connect_to_prodev()
    create_table(db_conn)

    user_data = read_csv_data(CSV_FILE)
    insert_data(db_conn, user_data)
    db_conn.close()
