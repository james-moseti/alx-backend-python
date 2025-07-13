import time
import sqlite3 
import functools

def with_db_connection(func):
    """
    Decorator that automatically handles opening and closing database connections.
    Opens a connection, passes it as the first argument to the function, and closes it afterward.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Open database connection
        conn = sqlite3.connect('users.db')
        
        try:
            # Call the original function with connection as first argument
            result = func(conn, *args, **kwargs)
            return result
        finally:
            # Always close the connection, even if an exception occurs
            conn.close()
    
    return wrapper

query_cache = {}

def cache_query(func):
    """
    Decorator that caches query results based on the SQL query string.
    Avoids redundant database calls by storing results in memory.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Extract the query parameter to use as cache key
        cache_key = None
        
        # Check if query is in kwargs
        if 'query' in kwargs:
            cache_key = kwargs['query']
        # Check if query is in positional arguments (assuming it's the second arg after conn)
        elif len(args) >= 2:
            cache_key = args[1]
        
        # If we found a query to use as cache key
        if cache_key:
            # Check if result is already cached
            if cache_key in query_cache:
                print(f"[CACHE] Cache hit for query: {cache_key}")
                return query_cache[cache_key]
            
            # If not cached, execute the function and cache the result
            print(f"[CACHE] Cache miss for query: {cache_key}")
            result = func(*args, **kwargs)
            query_cache[cache_key] = result
            print(f"[CACHE] Result cached for query: {cache_key}")
            return result
        else:
            # If no query parameter found, execute without caching
            print("[CACHE] No query parameter found, executing without caching")
            return func(*args, **kwargs)
    
    return wrapper

@with_db_connection
@cache_query
def fetch_users_with_cache(conn, query):
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor.fetchall()

#### First call will cache the result
users = fetch_users_with_cache(query="SELECT * FROM users")

#### Second call will use the cached result
users_again = fetch_users_with_cache(query="SELECT * FROM users")