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

@with_db_connection 
def get_user_by_id(conn, user_id): 
    cursor = conn.cursor() 
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,)) 
    return cursor.fetchone() 

#### Fetch user by ID with automatic connection handling 
user = get_user_by_id(user_id=1)
print(user)