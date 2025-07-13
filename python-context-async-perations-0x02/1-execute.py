import sqlite3

class ExecuteQuery:
    def __init__(self, db_path, query, params=None):
        self.db_path = db_path
        self.query = query
        self.params = params or ()
        self.connection = None
        self.result = None
    
    def __enter__(self):
        self.connection = sqlite3.connect(self.db_path)
        cursor = self.connection.cursor()
        cursor.execute(self.query, self.params)
        self.result = cursor.fetchall()
        return self.result
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            self.connection.close()

# Setup sample data
with sqlite3.connect("example.db") as conn:
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
    cursor.execute("INSERT OR IGNORE INTO users (name, age) VALUES ('Alice', 28), ('Bob', 35), ('Charlie', 22), ('Diana', 31)")

# Use the ExecuteQuery context manager
with ExecuteQuery("example.db", "SELECT * FROM users WHERE age > ?", (25,)) as result:
    print(result)