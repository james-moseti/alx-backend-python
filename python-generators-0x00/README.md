# CSV to MySQL Import

A Python script that imports user data from a CSV file into a MySQL database.

## Prerequisites

- Python 3.x
- MySQL Server
- `mysql-connector-python` package

```bash
pip install mysql-connector-python
```

## Setup

1. Update MySQL credentials in the script:
   ```python
   MYSQL_CONFIG = {
       'user': 'root',
       'password': 'your_password',  # Replace with your MySQL password
       'host': 'localhost',
   }
   ```

2. Ensure your CSV file (`user_data.csv`) has the following format:
   ```
   name,email,age
   John Doe,john@example.com,25.5
   Jane Smith,jane@example.com,30.0
   ```

## Usage

```bash
python script_name.py
```

The script will:
- Create the `ALX_prodev` database if it doesn't exist
- Create the `user_data` table with columns: `user_id`, `name`, `email`, `age`
- Import CSV data, skipping duplicates based on email
- Generate unique UUIDs for each user

## Database Schema

| Column   | Type         | Description |
|----------|--------------|-------------|
| user_id  | CHAR(36)     | Primary key (UUID) |
| name     | VARCHAR(255) | User's name |
| email    | VARCHAR(255) | User's email (indexed) |
| age      | DECIMAL(5,2) | User's age |

## Features

- Automatic database and table creation
- Duplicate email prevention
- UUID generation for unique user IDs
- Error handling for database connections