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

def retry_on_failure(retries=3, delay=2):
    """
    Decorator that retries a function a specified number of times if it raises an exception.
    
    Args:
        retries (int): Number of retry attempts (default: 3)
        delay (int): Delay in seconds between retries (default: 2)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(retries + 1):  # +1 for the initial attempt
                try:
                    # Try to execute the function
                    result = func(*args, **kwargs)
                    if attempt > 0:
                        print(f"[RETRY] Function succeeded on attempt {attempt + 1}")
                    return result
                except Exception as e:
                    last_exception = e
                    
                    if attempt < retries:  # Don't sleep after the last attempt
                        print(f"[RETRY] Attempt {attempt + 1} failed: {e}. Retrying in {delay} seconds...")
                        time.sleep(delay)
                    else:
                        print(f"[RETRY] All {retries + 1} attempts failed. Giving up.")
            
            # If we get here, all attempts have failed
            raise last_exception
        
        return wrapper
    return decorator

@with_db_connection
@retry_on_failure(retries=3, delay=1)
def fetch_users_with_retry(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    return cursor.fetchall()

#### attempt to fetch users with automatic retry on failure
users = fetch_users_with_retry()
print(users)