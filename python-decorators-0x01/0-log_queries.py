import sqlite3
import functools

def log_queries(func):
    """
    Decorator that logs SQL queries before executing the decorated function.
    Assumes the function takes a 'query' parameter.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Extract the query parameter
        query = None
        
        # Check if query is in kwargs
        if 'query' in kwargs:
            query = kwargs['query']
        # Check if query is the first positional argument
        elif args:
            query = args[0]
        
        # Log the query if found
        if query:
            print(f"[SQL QUERY LOG] Executing: {query}")
        else:
            print("[SQL QUERY LOG] No query parameter found")
        
        # Execute the original function
        return func(*args, **kwargs)
    
    return wrapper

@log_queries
def fetch_all_users(query):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results

#### fetch users while logging the query
users = fetch_all_users(query="SELECT * FROM users")